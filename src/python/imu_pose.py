import time
import board
import digitalio
import adafruit_lis3dh
import math
import os

i2c = board.I2C()
# int1 = digitalio.DigitalInOut(board.D17)
# lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c)
full_path = __file__
file_name = os.path.basename(full_path)


class Pose:
    UNKNWON = -1
    VERTICAL_UP = 0
    VERTICAL_DOWN = 1
    HORIZONTAL_A = 2
    HORIZONTAL_B = 3
    HORIZONTAL_C = 4


name_dict = {
    -1: "UNKNWON",
    0: "VERTICAL_UP",
    1: "VERTICAL_DOWN",
    2: "HORIZONTAL_A",
    3: "HORIZONTAL_B",
    4: "HORIZONTAL_C",
}


def accel_to_position_state(ax, ay, az):
    state = Pose.UNKNWON

    # up and degree < 30
    if az > 8.5:
        state = Pose.VERTICAL_UP
    # down and degree < 30
    elif az < -8.5:
        state = Pose.VERTICAL_DOWN
    # degree < 30
    elif abs(az) < 4.9:
        # horizontal state, but need to detailing
        if ay > 8.5:
            state = Pose.HORIZONTAL_A
        elif ax < 0 and ay > -8.5 and ay < 0:
            state = Pose.HORIZONTAL_B
        elif ax > 0 and ay > -8.5 and ay < 0:
            state = Pose.HORIZONTAL_C
        else:
            state = Pose.UNKNWON
    else:
        state = Pose.UNKNWON
    return state

def is_shaking():
    return lis3dh.shake(shake_threshold=15)

# Need to call this every time you want to get current pose
def get_pose():
    ax, ay, az = lis3dh.acceleration
    state = accel_to_position_state(ax, ay, az)
    print(f"{file_name}: get state {state}")
    return state

def get_acce():
    ax, ay, az = lis3dh.acceleration
    return ax, ay, az

def test():
    while True:
        ax, ay, az = lis3dh.acceleration
        print("raw accel data: ")
        print(f"ax = {ax}  ay = {ay}  az = {az}\n")

        roll = math.degrees(math.atan2(ay, az))
        pitch = math.degrees(-math.atan2(ax, az))

        print(f"roll = {roll}")
        print(f"pitch = {pitch}\n")

        state = accel_to_position_state(ax, ay, az)

        print(name_dict[state])
        print("")

        time.sleep(0.5)


# When az is closed to 10, the triangular prism is in vertical mode
# When az is closed to 0, the triangular prism is in horizontal mode

if __name__ == "__main__":
    # test()
    print(get_pose())
