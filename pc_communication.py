from time import sleep

import serial
from itertools import islice

PORT = "COM7"
CMD_GIVE_STATUS = "7E 32 30 30 30 34 36 34 32 45 30 30 32 30 30 46 44 33 37 0D"

ser = serial.Serial(
    port=PORT,
    baudrate=19200,
    timeout=0.1)


def singed_int(hexstr: str, bits: int):
    value = int(hexstr, 16)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value


print("Connected to: " + ser.portstr)
print("Name:", ser.name)
print("---Writing---")
try:
    while True:
        ser.write(bytes.fromhex(CMD_GIVE_STATUS))
        received = ser.readline()
        HEX_RECEIVED = str(received)[13:]
        CHUNKS_STATUS = [2, 1, 32, 1, 12, 2, 2, 5, 2, 16]
        DOUBLE_CHUNKS_STATUS = [i * 2 for i in CHUNKS_STATUS]
        assert len(HEX_RECEIVED) >= sum(DOUBLE_CHUNKS_STATUS), "Some data are missing"
        it = iter(str(HEX_RECEIVED)[2:])
        result = [''.join(islice(it, i)) for i in DOUBLE_CHUNKS_STATUS]
        _, NUMBER_OF_CELLS, VOLTAGE_OF_CELLS, NUMBER_OF_TEMPERATURES, CELL_TEMPERATURES, CURRENT_CURRENT, \
            CURRENT_VOLTAGE, one, SOC, two = result
        print("SOC:", (int(SOC, base=16) / 10), "%,CURRENT:", singed_int(CURRENT_CURRENT, 16) / 100, "A, VOLTAGE:",
              (int(CURRENT_VOLTAGE, base=16) / 100))
        sleep(1)
except KeyboardInterrupt:
    ser.close()
    print("Finished")
