from machine import RTC, Pin, I2C
from ds3231 import DS3231

clock = DS3231(I2C(0, scl=Pin(21), sda=Pin(20)))
rtc = RTC()


def synchronization():
    try:
        rtc.datetime(clock.get_time())
        return False
    except BaseException:
        return True


def out_of_limits(min: int, value: int or float, max: int):
    if min <= value <= max:
        return value
    raise ValueError(min, value, max)


def singed_int(hexstr: str):
    value = int(hexstr, 16)
    if value & (1 << (16 - 1)):
        value -= 1 << 16
    return value