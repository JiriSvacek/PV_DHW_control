"""Module with classes."""
import time
import lcd_0inch96
import ubinascii
import machine


class Heater:
    """Class Heater."""

    def __init__(
        self,
        pin: machine.Pin,
        start_soc: int,
        stop_soc: int,
        stop_current: int,
        start_current: int,
    ) -> None:
        self.start_soc = start_soc
        self.stop_soc = stop_soc
        self.flag_stop_current = stop_current
        self.flag_start_current = start_current
        self.flag_bit_current = False
        self.flag_bit_soc_ok = False
        self.change = False
        self.last_status = 0
        self.pin = pin

    @staticmethod
    def _fully_charged_condition(act_current: float, act_soc: float):
        return -6 <= act_current <= 6 and act_soc >= 99.3

    def _over_current_reset_condition(
        self,
        act_soc: float,
        act_current: float,
        slave_status: bool,
        master_status: bool,
    ) -> bool:
        return (
            (
                act_current > self.flag_start_current
                or self._fully_charged_condition(act_current, act_soc)
            )
            and self.flag_bit_current
            and not slave_status
            and master_status
        )

    def _value_change_check(self) -> None:
        if self.value() != self.last_status:
            self.change = True
        else:
            self.change = False
        self.last_status = self.value()

    def _control(
        self,
        act_soc: float,
        act_current: float,
        current_slave_status: bool,
        current_master_status: bool,
    ) -> None:
        if (
            act_soc > self.start_soc
            and not self.flag_bit_current
            and (act_current > 0 or self._fully_charged_condition(act_current, act_soc))
            and current_master_status
        ):
            self.flag_bit_soc_ok = True
        if self._over_current_reset_condition(
            act_soc, act_current, current_slave_status, current_master_status
        ):
            self.flag_bit_current = False
        if (
            act_current < self.flag_stop_current
            and not self.flag_bit_current
            and not current_slave_status
            and self.flag_bit_soc_ok
        ):
            self.flag_bit_current = True
        if act_soc < self.stop_soc:
            self.flag_bit_soc_ok = False
            self.flag_bit_current = False

    def set(
        self,
        act_soc: float,
        act_current: float,
        slave_change: bool,
        current_master_status: bool,
        act_line_power: int,
        power_master_status: bool,
    ) -> None:
        """Main control method."""
        if (
            act_line_power < 12 or act_line_power < 26 and self.value()
        ) and power_master_status:
            self._control(act_soc, act_current, slave_change, current_master_status)
            if self.flag_bit_soc_ok and not self.flag_bit_current:
                self.on()
            else:
                self.off()
        else:
            if not slave_change:
                self.off()
        self._value_change_check()

    def on(self) -> None:
        """Set pin on."""
        self.pin.value(1)

    def off(self) -> None:
        """Set pin off."""
        self.pin.value(0)

    def value(self) -> bool:
        """Get boolean pin value."""
        if self.pin.value() == 1:
            return True
        return False

    def all_stop(self) -> None:
        """Clear all setting atribute and set pin to low."""
        self.flag_bit_soc_ok = False
        self.flag_bit_current = False
        self.change = False
        self.last_status = 0
        self.off()


class Counter:
    """Counter class with pin.irq."""

    def __init__(self, pin: machine.Pin):
        self.pin = pin
        self.pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.trigger_count)
        self.counter = 0

    def trigger_count(self, pin: machine.Pin) -> None:
        """Count up counter"""
        self.counter += 1

    def zero_counter(self) -> None:
        """Zero counter."""
        self.counter = 0

    def get_count(self) -> int:
        """Get counter and zero it."""
        count = self.counter
        self.zero_counter()
        return count


class LCD:
    """LCD parrent class."""

    _blue = lcd_0inch96.BLUE
    _white = lcd_0inch96.WHITE
    _black = lcd_0inch96.BLACK

    def __init__(
        self, lcd: lcd_0inch96.LCD_0inch96, pin: machine.Pin, timer: machine.Timer
    ):
        self.lcd = lcd
        self.lcd.write_cmd(0x36)
        self.lcd.write_data(0x70)
        self.button = pin
        self.button.irq(
            trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING,
            handler=self._telemetry_show,
        )
        self.timer = timer
        self.offline_telemetry = False
        self.ticks = time.ticks_ms()

    def _telemetry_hide(self, timer: machine.Timer) -> None:
        self.offline_telemetry = False

    def _telemetry_show(self, pin: machine.Pin) -> None:
        if not self.offline_telemetry and self.button.value() == 0:
            self.ticks = time.ticks_ms()
            self.offline_telemetry = True
        if (
            self.offline_telemetry
            and self.button.value() == 1
            and time.ticks_ms() > (self.ticks + 100)
        ):
            self.timer.init(
                mode=machine.Timer.ONE_SHOT, period=2000, callback=self._telemetry_hide
            )

    def show_battery_params(self, soc: float, current: float, voltage: float) -> None:
        """Show battery parameters."""
        self.lcd.fill(self._black)
        self.lcd.text(f"Voltage: {float(voltage):6.2f} V", 12, 6, self._blue)
        self.lcd.text(f"Current: {float(current):6.2f} A", 12, 26, self._blue)
        self.lcd.text(f"SOC:     {float(soc):6.1f} %", 12, 46, self._blue)
        self.add_time()
        self.display()

    def add_time(self) -> None:
        """Text field with actual time and date."""
        act = time.localtime()
        time_str = (
            f"{act[3]:2d}:{act[4]:02d}:{act[5]:02d} {act[2]:2d}.{act[1]:2d}.{act[0]:4d}"
        )
        self.lcd.text(time_str, 4, 66, self._blue)

    def display(self) -> None:
        """Display texts from buffer."""
        self.lcd.display()

    def error_loop(self) -> None:
        """Show error on screen in infinite loop."""
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

    def offline_screen(self) -> None:
        """Show screen when offline."""
        self.lcd.fill(self._black)
        self.lcd.text("Heaters are OFF", 21, 6, self._blue)
        self.lcd.text("Planned start in:", 13, 26, self._blue)
        act = time.localtime()
        hours_left = 24 if act[3] >= 8 else 0
        left_str = (
            f"{8 + hours_left - 1 - act[3]:3d}:{60 - 1 - act[4]:02d}:{60 - act[5]:02d}"
        )
        self.lcd.text(left_str, 40, 46, self._blue)
        self.add_time()
        self.display()


class PowerPlant:
    """Power plant class wich controls heaters acording to read parameters from battery."""

    def __init__(
        self,
        heater_70: Heater,
        tank: Heater,
        rs485: machine.UART,
        counter_l1: Counter,
        counter_l2: Counter,
    ) -> None:
        self.heater_70 = heater_70
        self.tank = tank
        self.rs485 = rs485
        self.counter_l1 = counter_l1
        self.counter_l2 = counter_l2
        self.counter_connection_error = 0

    def heaters_all_stop(self) -> None:
        """Stop all heaters."""
        self.heater_70.all_stop()
        self.tank.all_stop()

    @staticmethod
    def out_of_limits(minimum: int, value: float, maxximum: int) -> float:
        """Check value if in the limits."""
        if minimum <= value <= maxximum:
            return value
        raise ValueError(minimum, value, maxximum)

    @staticmethod
    def singed_int(hexstr: str) -> int:
        """Convers hex to singed int."""
        value = int(hexstr, 16)
        if value & (1 << (16 - 1)):
            value -= 1 << 16
        return value

    def read_battery_parameters(self, command: str) -> tuple[bool, float, float, float]:
        """Read telemetry data from batter."""
        try:
            self.rs485.write(ubinascii.unhexlify(command))
            time.sleep(0.125)
            if self.rs485.any():
                data = str(self.rs485.readline())[15:]
                response = (
                    False,
                    self.out_of_limits(0, int("0x" + data[114:118]) / 10, 100),
                    self.out_of_limits(-100, self.singed_int(data[96:100]) / 100, 100),
                    self.out_of_limits(0, int("0x" + data[100:104]) / 100, 100),
                )
            else:
                raise TypeError
        except (TypeError, ValueError):
            if self.counter_connection_error < 4:
                if self.counter_connection_error > 1:
                    self.heaters_all_stop()
                self.counter_connection_error += 1
                time.sleep(1)
                return self.read_battery_parameters(command)
            return True, 0, -100, 0
        self.counter_connection_error = 0
        return response

    def _get_counters_data(self) -> tuple[int, int]:
        return self.counter_l1.get_count(), self.counter_l2.get_count()

    def zero_counters(self) -> None:
        """Zero all counters."""
        self.counter_l1.zero_counter()
        self.counter_l2.zero_counter()

    def set_heaters(self, soc: float, current: float) -> None:
        """Set all heaters according to input values."""
        count_l1, count_l2 = self._get_counters_data()
        self.tank.set(
            soc, current, False, self.heater_70.value(), count_l1, True
        )  # heater_301.value())
        self.heater_70.set(
            soc, current, self.tank.change, True, count_l2, True
        )  # heater_301.value(), count_L2, True)
        # heater_301.set(SOC, current, heater_70.change or tank.change, True, count_L1, True)
