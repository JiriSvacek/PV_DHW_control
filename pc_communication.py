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
    ser = serial.Serial(port=port, baudrate=19200, timeout=0.1)
    print("Connected to: " + ser.portstr)
    print("Name:", ser.name)
    print("---Writing---")
    try:
        while True:
            ser.write(bytes.fromhex(cmd_give_status))
            received = ser.readline()
            hex_received = str(received)[13:]
            chunks_status = [2, 1, 32, 1, 12, 2, 2, 5, 2, 16]
            double_chunks_status = [i * 2 for i in chunks_status]
            assert len(hex_received) >= sum(
                double_chunks_status
            ), "Some data are missing"
            it = iter(str(hex_received)[2:])
            result = ["".join(islice(it, i)) for i in double_chunks_status]
            (
                _,
                number_of_cells,
                voltage_of_cells,
                number_of_temperatures,
                cell_temperatures,
                actual_current,
                actual_voltage,
                one,
                soc,
                two,
            ) = result
            print(
                "SOC:",
                (int(soc, base=16) / 10),
                "%,CURRENT:",
                singed_int(actual_current, 16) / 100,
                "A, VOLTAGE:",
                (int(actual_voltage, base=16) / 100),
            )
            time.sleep(1)
    except KeyboardInterrupt:
        ser.close()
        print("Finished")


if __name__ == "__main__":
    main()
