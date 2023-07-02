from lcd_0inch96 import LCD_0inch96, BLACK, GREEN, BLUE, WHITE, RED
from support_functions import synchronization, out_of_limits, singed_int
from ubinascii import unhexlify
from time import sleep, localtime, time
from models import Heater
from machine import Pin, UART

last_sync = localtime()[2]
last_cycle = time()
CMD_GIVE_TELEMETRY = "7E3230303034363432453030323030464433370D"
counter_connection_error = 0
counter_L1 = 0
counter_L2 = 0

heater_301 = Heater(6, 65, 50, -40, 14)
heater_70 = Heater(7, 82, 70, -40, 14)
tank = Heater(14, 92, 86, -40, 20)

power_L1 = Pin(26, Pin.IN, Pin.PULL_DOWN)
power_L2 = Pin(27, Pin.IN, Pin.PULL_DOWN)

uart0 = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(1))
button_A = Pin(15, Pin.IN, Pin.PULL_UP)
lcd = LCD_0inch96()
lcd.write_cmd(0x36)
lcd.write_data(0x70)

sleep(1)


def zero_counters():
    global counter_L1
    global counter_L2
    counter_L1 = 0
    counter_L2 = 0


def trigger_count_L1(Pin):
    global counter_L1
    counter_L1 += 1


def trigger_count_L2(Pin):
    global counter_L2
    counter_L2 += 1


def heaters_all_stop():
    heater_70.all_stop()
    heater_301.all_stop()
    tank.all_stop()


def lcd_battery_status(SOC, current, voltage):
    lcd.text("Voltage: {0:6.2f} V".format(float(voltage)), 12, 6, BLUE)
    lcd.text("Current: {0:6.2f} A".format(float(current)), 12, 26, BLUE)
    lcd.text("SOC:     {0:6.1f} %".format(float(SOC)), 12, 46, BLUE)


def read_battery_parameters(command: str):
    global counter_connection_error
    try:
        uart0.write(unhexlify(command))
        sleep(0.125)
        if uart0.any():
            data = str(uart0.readline())[15:]
            response = (False, out_of_limits(0, int("0x" + data[114:118]) / 10, 100),
                        out_of_limits(-100, singed_int(data[96:100]) / 100, 100),
                        out_of_limits(0, int("0x" + data[100:104]) / 100, 100))
        else:
            raise TypeError
    except (TypeError, ValueError):
        if counter_connection_error < 4:
            if counter_connection_error > 1:
                heaters_all_stop()
            counter_connection_error += 1
            sleep(1)
            return read_battery_parameters(command)
        else:
            return True, 0, -100, 0
    else:
        counter_connection_error = 0
        return response


power_L1.irq(trigger=Pin.IRQ_FALLING, handler=trigger_count_L1)
power_L2.irq(trigger=Pin.IRQ_FALLING, handler=trigger_count_L2)
flag_error = synchronization()

while not flag_error:
    actual_time = localtime()
    if 8 <= actual_time[3] <= 18:
        if time() - last_cycle >= 2:
            count_L1 = counter_L1
            count_L2 = counter_L2
            zero_counters()
            last_cycle = time()
            flag_error, SOC, current, voltage = read_battery_parameters(CMD_GIVE_TELEMETRY)
            tank.set(SOC, current, False, heater_70.value(), count_L1, heater_301.value())
            heater_70.set(SOC, current, tank.change, heater_301.value(), count_L2, True)
            heater_301.set(SOC, current, heater_70.change or tank.change, True, count_L1, True)
            lcd.fill(BLACK)
            lcd_battery_status(SOC, current, voltage)
            print(count_L1, count_L2)
        else:
            sleep(0.1)
    else:
        zero_counters()
        lcd.fill(BLACK)
        heaters_all_stop()
        if button_A.value() == 0:
            flag_error, *battery_parameters = read_battery_parameters(CMD_GIVE_TELEMETRY)
            lcd_battery_status(*battery_parameters)
        else:
            hours_left = 24 if actual_time[3] >= 8 else 0
            difference = "{0:3d}:{1:02d}:{2:02d}".format(8 + hours_left - 1 - actual_time[3], 60 - 1 - actual_time[4],
                                                         60 - actual_time[5])
            lcd.text("Heaters are OFF", 21, 6, BLUE)
            lcd.text("Planned start in:", 13, 26, BLUE)
            lcd.text(difference, 40, 46, BLUE)
        sleep(0.5)
    if last_sync != actual_time[2] and 19 < actual_time[3]:
        flag_error = synchronization()
        last_sync = actual_time[2]

    time_string = "{0:2d}:{1:02d}:{2:02d} {3:2d}.{4:2d}.{5:4d}".format(actual_time[3], actual_time[4], actual_time[5],
                                                                       actual_time[2], actual_time[1], actual_time[0])
    lcd.text(time_string, 4, 66, BLUE)
    lcd.display()

heaters_all_stop()
error_show = False

while True:
    lcd.fill(WHITE)
    lcd.hline(0, 10, 160, BLUE)
    lcd.hline(0, 70, 160, BLUE)
    if error_show:
        lcd.text("Power plant in error", 0, 35, BLUE)
        error_show = False
    else:
        error_show = True
    lcd.display()
    sleep(1)
