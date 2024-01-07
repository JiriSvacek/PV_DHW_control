import lcd_0inch96
import ds3231
import machine
import models
import time

def synchronization(clock: ds3231.DS3231) -> bool:
    try:
        machine.RTC().datetime(clock.get_time())
        return False
    except BaseException:
        return True


def init() -> tuple[models.PowerPlant, ds3231.DS3231, models.LCD, int, float]:
    # Init object
    #heater_301 = Heater(6, 65, 50, -40, 14)
    heater_70 = models.Heater(machine.Pin(7, machine.Pin.OUT, value=0), 82, 70, -40, 14)
    tank = models.Heater(machine.Pin(14, machine.Pin.OUT, value=0), 92, 86, -40, 20)
    rs485 = machine.UART(0, baudrate=19200, tx=machine.Pin(0), rx=machine.Pin(1))
    counter_L1 = models.Counter(machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_DOWN))
    counter_L2 = models.Counter(machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_DOWN))
    power_plant = models.PowerPlant(heater_70, tank, rs485, counter_L1, counter_L2)
    # Init object
    clock = ds3231.DS3231(machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20)))
    # Init object
    lcd = models.LCD(lcd_0inch96.LCD_0inch96(), machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP))
    return power_plant, clock, lcd, time.localtime()[2], time.time()


def main() -> None:
    send_telemetry = "7E3230303034363432453030323030464433370D"
    power_plant, clock, lcd, last_sync, last_cycle = init()
    flag_error = synchronization(clock)
    while not flag_error:
        actual_time = time.localtime()
        if 8 <= actual_time[3] <= 18:
            if time.time() - last_cycle >= 2:
                last_cycle = time.time()
                flag_error, SOC, current, voltage = power_plant.read_battery_parameters(send_telemetry)
                power_plant.set_heaters(SOC, current)
                lcd.show_battery_params(SOC, current, voltage)
            else:
                time.sleep(0.1)
        else:
            power_plant.zero_counters()
            power_plant.heaters_all_stop()
            if lcd.offline_telemetry:
                flag_error, *battery_parameters = power_plant.read_battery_parameters(send_telemetry)
                lcd.show_battery_params(*battery_parameters)
            else:
                lcd.offline_screen(actual_time)
            time.sleep(0.5)
        if last_sync != actual_time[2] and 19 < actual_time[3]:
            flag_error = synchronization(clock)
            last_sync = actual_time[2]
        lcd.add_time(actual_time)
        lcd.display()
    power_plant.heaters_all_stop()
    lcd.error_loop()
    
if __name__ == "__main__":
    main()