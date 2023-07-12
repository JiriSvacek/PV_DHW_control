from machine import Pin


def _fully_charged_condition(act_current, act_SOC):
    return -6 <= act_current <= 6 and act_SOC >= 99.8


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
        self.pin = Pin(pin, Pin.OUT, value=0)

    def _over_current_reset_condition(self, act_SOC, act_current, slave_status, master_status):
        return (act_current > self.flag_start_current or _fully_charged_condition(act_current, act_SOC)) \
               and self.flag_bit_current and not slave_status and master_status

    def _value_change_check(self):
        if self.value() != self.last_status:
            self.change = True
        else:
            self.change = False
        self.last_status = self.value()

    def _control(self, act_SOC, act_current, current_slave_status, current_master_status):
        if act_SOC > self.start_SOC and not self.flag_bit_current and (
                act_current > 0 or _fully_charged_condition(act_current, act_SOC)) and current_master_status:
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
