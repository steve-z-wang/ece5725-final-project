
from imu_pose import get_acce

import os
import time
import board

fifo_path = "/tmp/accel_fifo"

position = get_acce()

def write_accel_data_to_fifo():
    while True:
        ax, ay, az = position.get_acce()

        with open(fifo_path, "w") as fifo:
            fifo.write(f"{ax},{ay},{az}\n")

        time.sleep(0.5)

if __name__ == "__main__":
    write_accel_data_to_fifo()

