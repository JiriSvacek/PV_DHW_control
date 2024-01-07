"""Module for synchronize time Pi Pico RTC with DS3231 Pi pico module RTC."""
import ds3231
import machine


def main():
    clock = ds3231.DS3231(machine.I2C(0, scl=machine.Pin(21), sda=machine.Pin(20)))
    clock.set_time()


if __name__ == "__main__":
    main()