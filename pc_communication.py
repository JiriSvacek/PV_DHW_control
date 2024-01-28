"""Script for reading data from RS485 via USB to PC"""
import time
from itertools import islice
import serial


def singed_int(hexstr: str, bits: int) -> int:
    """Convert to singed int."""
    value = int(hexstr, 16)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


def main() -> None:
    """Main function call."""
    port = "COM7"
    cmd_give_status = "7E 32 30 30 30 34 36 34 32 45 30 30 32 30 30 46 44 33 37 0D"
    info_size = 75  # bytes
    chunks_status = {  # according to seplos bms protocol v2.0, number represents bytes, total 75
        "data_flag": 1,
        "command_group": 1,
        "number_of_cells": 1,
        "cells_voltage_array": 32,
        "number_of_temperatures": 1,
        "temperatures_array": 12,
        "current": 2,
        "battery_voltage": 2,
        "residual_capacity": 2,
        "custom_number": 1,
        "battery_capacity": 2,
        "SOC": 2,
        "rated_capacity": 2,
        "number_of_cycles": 2,
        "SOH": 2,
        "port_voltage": 2,
        "reserve1": 2,
        "reserve2": 2,
        "reserve3": 2,
        "reserve4": 2,
    }
    ser = serial.Serial(port=port, baudrate=19200, timeout=0.1)
    print("Connected to: " + ser.portstr)
    print("Name:", ser.name)
    print("---Writing---")
    try:
        while True:
            ser.write(bytes.fromhex(cmd_give_status))
            received = ser.readline()
            message_start = 15  # first 15 is respone status
            message_finished = (
                message_start + info_size * 2  # trim out end of line
            )  # info _size * 2 -> bytes to hex
            hex_received = str(received)[
                message_start:message_finished
            ]  # trim recivied.
            double_chunks_status = [i * 2 for i in chunks_status.values()]
            assert len(hex_received) == sum(
                double_chunks_status
            ), "Messsage has wrong lenght."
            it = iter(str(hex_received))
            result = ["".join(islice(it, i)) for i in double_chunks_status]
            # hex to dec representers -> cell_voltage(mV), temperature(0.1 °C), capacity(0.01 Ah)
            # SOH, SOC (1‰), port/battery voltage(0.01V), current (signed int, 0.01A)
            output_hex = dict(zip(chunks_status.keys(), result))
            print(
                "SOC:",
                (int(output_hex["SOC"], base=16) / 10),
                "%,CURRENT:",
                singed_int(output_hex["current"], 16) / 100,
                "A, VOLTAGE:",
                (int(output_hex["battery_voltage"], base=16) / 100),
            )
            time.sleep(1)
    except KeyboardInterrupt:
        ser.close()
        print("Finished")


if __name__ == "__main__":
    main()
