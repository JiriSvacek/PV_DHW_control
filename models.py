import lcd_0inch96
import ubinascii
import time
import machine


class Heater:

    def __init__(self, pin: int, start_SOC: int, stop_SOC: int, stop_current: int, start_current: int):
        self.start_SOC = start_SOC
        self.stop_SOC = stop_SOC
        self.flag_stop_current = stop_current
        self.flag_start_current = start_current
        self.flag_bit_current = False
        self.flag_bit_SOC_OK = False
        self.change = False
        self.last_status = 0
        self.pin = machine.Pin(pin, machine.Pin.OUT, value=0)

    @staticmethod
    def _fully_charged_condition(act_current, act_SOC):
        return -6 <= act_current <= 6 and act_SOC >= 99.3

    def _over_current_reset_condition(self, act_SOC, act_current, slave_status, master_status):
        return (act_current > self.flag_start_current or self._fully_charged_condition(act_current, act_SOC)) \
               and self.flag_bit_current and not slave_status and master_status

    def _value_change_check(self):
        if self.value() != self.last_status:
            self.change = True
        else:
            self.change = False
        self.last_status = self.value()

    def _control(self, act_SOC, act_current, current_slave_status, current_master_status):
        if act_SOC > self.start_SOC and not self.flag_bit_current and (
                act_current > 0 or self._fully_charged_condition(act_current, act_SOC)) and current_master_status:
            self.flag_bit_SOC_OK = True
        if self._over_current_reset_condition(act_SOC, act_current, current_slave_status, current_master_status):
            self.flag_bit_current = False
        if act_current < self.flag_stop_current and not self.flag_bit_current and not current_slave_status \
                and self.flag_bit_SOC_OK:
            self.flag_bit_current = True
        if act_SOC < self.stop_SOC:
            self.flag_bit_SOC_OK = False
            self.flag_bit_current = False

    def set(self, act_SOC: float, act_current: float, slave_change: bool, current_master_status: bool,
            act_line_power: int, power_master_status: bool):
        if (act_line_power < 12 or act_line_power < 26 and self.value()) and power_master_status:
            self._control(act_SOC, act_current, slave_change, current_master_status)
            if self.flag_bit_SOC_OK and not self.flag_bit_current:
                self.on()
            else:
                self.off()
        else:
            if not slave_change:
                self.off()
        self._value_change_check()

    def on(self):
        self.pin.value(1)

    def off(self):
        self.pin.value(0)

    def value(self):
        if self.pin.value() == 1:
            return True
        return False

    def all_stop(self):
        self.flag_bit_SOC_OK = False
        self.flag_bit_current = False
        self.change = False
        self.last_status = 0
        self.off()


class Counter:

    def __init__(self, pin):
        self.pin = pin
        self.pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.trigger_count)
        self.counter = 0

    def trigger_count(self, Pin):
        self.counter += 1


    def zero_counter(self):
        self.counter_L1 = 0

    def get_count(self):
        count = self.counter
        self.zero_counter()
        return count

    
class LCD:
    _blue = lcd_0inch96.BLUE
    _white = lcd_0inch96.WHITE
    _black = lcd_0inch96.BLACK

    def __init__(self, lcd, pin):
        self.lcd = lcd
        self.lcd.write_cmd(0x36)
        self.lcd.write_data(0x70)
        self.button = pin
        self.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self._telemetry_show)
        self.offline_telemetry = False

    def _telemetry_hide(self, timer):
        self.offline_telemetry = False
        self.button.irq.handler = self._telemetry_show
    
    def _telemetry_show(self, pin):
        pin.irq.handler = None
        self.offline_telemetry = True
        machine.Timer.init(mode=machine.Timer.ONE_SHOT, period=2000, callback=self._telemetry_hide)

    def show_battery_params(self, SOC, current, voltage):
        self.lcd.fill(self._black)
        self.lcd.text("Voltage: {0:6.2f} V".format(float(voltage)), 12, 6, self._blue)
        self.lcd.text("Current: {0:6.2f} A".format(float(current)), 12, 26, self._blue)
        self.lcd.text("SOC:     {0:6.1f} %".format(float(SOC)), 12, 46, self._blue)

    def add_time(self, actual_time):
        time_string = "{0:2d}:{1:02d}:{2:02d} {3:2d}.{4:2d}.{5:4d}".format(actual_time[3], actual_time[4], actual_time[5],
                                                                       actual_time[2], actual_time[1], actual_time[0])
        self.lcd.text(time_string, 4, 66, self._blue)

    def display(self):
        self.lcd.display()
    
    def error_loop(self):
        error_show = True
        while True:
            self.lcd.fill(self._white)
            self.lcd.hline(0, 10, 160, self._blue)
            self.lcd.hline(0, 70, 160, self._blue)
            if error_show:
                self.lcd.text("Power plant in error", 0, 35, self._blue)
            error_show ^= True
            self.display()
            time.sleep(1)
    
    def offline_screen(self, actual_time):
        self.lcd.fill(self._black)
        hours_left = 24 if actual_time[3] >= 8 else 0
        difference = "{0:3d}:{1:02d}:{2:02d}".format(8 + hours_left - 1 - actual_time[3], 60 - 1 - actual_time[4],
                                                     60 - actual_time[5])
        self.lcd.text("Heaters are OFF", 21, 6, self._blue)
        self.lcd.text("Planned start in:", 13, 26, self._blue)
        self.lcd.text(difference, 40, 46, self._blue)


class PowerPlant:

    def __init__(self, heater_70, tank, rs485, counter_L1: Counter, counter_L2: Counter):
        self.heater_70 = heater_70
        self.tank = tank
        self.rs485 = rs485
        self.counter_L1 = counter_L1
        self.counter_L2 = counter_L2
        self.counter_connection_error = 0
        self.counter_L1 = 0
        self.counter_L2 = 0
    
    def heaters_all_stop(self):
        self.heater_70.all_stop()
        self.tank.all_stop()

    @staticmethod
    def out_of_limits(min: int, value: int or float, max: int):
        if min <= value <= max:
            return value
        raise ValueError(min, value, max)
    
    @staticmethod
    def singed_int(hexstr: str):
        value = int(hexstr, 16)
        if value & (1 << (16 - 1)):
            value -= 1 << 16
        return value

    def read_battery_parameters(self, command: str):
        try:
            self.rs485.write(ubinascii.unhexlify(command))
            time.sleep(0.125)
            if self.rs485.any():
                data = str(self.rs485.readline())[15:]
                response = (False, self.out_of_limits(0, int("0x" + data[114:118]) / 10, 100),
                            self.out_of_limits(-100, self.singed_int(data[96:100]) / 100, 100),
                            self.out_of_limits(0, int("0x" + data[100:104]) / 100, 100))
            else:
                raise TypeError
        except (TypeError, ValueError):
            if self.counter_connection_error < 4:
                if self.counter_connection_error > 1:
                    self.heaters_all_stop()
                self.counter_connection_error += 1
                time.sleep(1)
                return self.read_battery_parameters(command)
            else:
                return True, 0, -100, 0
        else:
            self.counter_connection_error = 0
            return response
        
    def _get_counters_data(self):
        return self.counter_L1.get_count(), self.counter_L2.get_count()
    
    def zero_counters(self):
        self.counter_L1.zero_counter()
        self.counter_L2.zero_counter()

    def set_heaters(self, SOC, current):
        count_L1, count_L2 = self._get_counters_data()
        self.tank.set(SOC, current, False, self.heater_70.value(), count_L1, True)#heater_301.value())
        self.heater_70.set(SOC, current, self.tank.change, True, count_L2, True) #heater_301.value(), count_L2, True)
        #heater_301.set(SOC, current, heater_70.change or tank.change, True, count_L1, True)

class PinInterruptHandler:

    def __init__(self):
        self.value = 0  # Initial value
        self._pin = Pin(2, Pin.IN)  # Replace '2' with your pin number
        self._pin.irq(trigger=Pin.IRQ_FALLING, handler=self._interrupt_handler)
        
    def _interrupt_handler(self, pin):
        # This method will be called when the interrupt occurs
        self._value += 1

    def get_value(self):
        return self._value