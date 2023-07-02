from ds3231 import DS3231
from machine import RTC, I2C, Pin

rtc = RTC()

clock = DS3231(I2C(0, scl=Pin(21), sda=Pin(20)))

clock.set_time()
