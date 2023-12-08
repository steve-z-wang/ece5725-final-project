import random
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import random
import math
from imu_pose import get_acce
import os
import time
fifo_path = "/tmp/accel_fifo"

import numpy as np


from canvas import Canvas 

fifo_path = "/tmp/matrix_fifo"
def update_fifo(matrix, fifo_path):
    try:
        # Get the raw RGB matrix data
        matrix_data = matrix.GetImage().tobytes()

        # Write the matrix data to the FIFO file
        with open(fifo_path, 'wb') as fifo:
            fifo.write(matrix_data)
    except Exception as e:
        print(f"Error updating FIFO: {e}")


class Grain:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0

class Adafruit_PixelDust:
    def __init__(self, w, h, n, s, e, sort):
        self.width = w
        self.height = h
        self.w8 = (w + 7) // 8
        self.xMax = w * 256 - 1
        self.yMax = h * 256 - 1
        self.n_grains = n
        self.scale = s
        self.elasticity = e
        self.sort = sort
        self.bitmap = None
        self.grain = None

    def get_bitmap(self):
        return bytes(self.bitmap)
    def update_fifo(self, fifo_path):
        try:
            with open(fifo_path, 'wb') as fifo:
                fifo.write(self.get_bitmap())
        except Exception as e:
            print(f"Error updating FIFO: {e}")

    def begin(self):
        if self.bitmap:
            return True  # Already allocated

        self.bitmap = bytearray([0] * (self.w8 * self.height))

        if self.bitmap:
            if not self.n_grains or self.grain is None:
                self.grain = [Grain() for _ in range(self.n_grains)]
                return True  # Success

            del self.bitmap  # Second alloc failed; free first-alloc data too

        return False  # You LOSE, good DAY sir!

    def set_pixel(self, x, y):
        x, y = int(x), int(y)
        self.bitmap[y * self.w8 + x // 8] |= (0x80 >> (x & 7))

    def clear_pixel(self, x, y):
        x, y = int(x), int(y)
        self.bitmap[y * self.w8 + x // 8] &= ~(0x80 >> (x & 7))

    def get_pixel(self, x, y):
        x, y = int(x), int(y)
        return bool(self.bitmap[y * self.w8 + x // 8] & (0x80 >> (x & 7)))

    def set_position(self, i, x, y):
        if self.get_pixel(x, y):
            return False  # Position already occupied

        self.set_pixel(x, y)
        self.grain[i].x = x * 256
        self.grain[i].y = y * 256
        return True

    def get_position(self, i):
        return self.grain[i].x // 256, self.grain[i].y // 256

    def randomize(self):
        for i in range(self.n_grains):
            while not self.set_position(i, random.randint(0, self.width - 1), random.randint(0, self.height - 1)):
                pass

    def clear(self):
        if self.bitmap:
            self.bitmap = bytearray([0] * (self.w8 * self.height))

    def bounce(self, n):
        return (-n * self.elasticity) // 256

    def iterate(self, ax, ay, az):
        ax = (ax * self.scale) // 256
        ay = (ay * self.scale) // 256
        az = abs(az * self.scale) // 2048

        az = max(1, min(5, 5 - az))  # Clip and invert

        ax -= az
        ay -= az

        az2 = az * 2 + 1  # Max random motion to add back in

        for i in range(self.n_grains):
            self.grain[i].vx += ax + random.randint(0, az2)
            self.grain[i].vy += ay + random.randint(0, az2)

            v2 = self.grain[i].vx**2 + self.grain[i].vy**2

            if v2 > 65536:  # If v^2 > 65536, then v > 256
                v = math.sqrt(v2)
                self.grain[i].vx = (256 * self.grain[i].vx) // v  # Maintain heading & limit magnitude
                self.grain[i].vy = (256 * self.grain[i].vy) // v

        if self.sort:
            q = int(math.atan2(ay, ax) * 8.0 / math.pi)  # -8 to +8
            q = (q + 1) // 2 if q >= 0 else (q + 16) // 2
            q = min(7, q)  # Ensure it's within bounds
            self.grain.sort(key=lambda g: (g.x, g.y))  # Sort grains by position, bottom-to-top

        for i in range(self.n_grains):
            new_x = self.grain[i].x + self.grain[i].vx
            new_y = self.grain[i].y + self.grain[i].vy

            if new_x < 0:
                new_x = 0
                self.grain[i].vx = self.bounce(self.grain[i].vx)

            elif new_x > self.xMax:
                new_x = self.xMax
                self.grain[i].vx = self.bounce(self.grain[i].vx)

            if new_y < 0:
                new_y = 0
                self.grain[i].vy = self.bounce(self.grain[i].vy)

            elif new_y > self.yMax:
                new_y = self.yMax
                self.grain[i].vy = self.bounce(self.grain[i].vy)

            old_idx = (self.grain[i].y // 256) * self.width + (self.grain[i].x // 256)
            new_idx = (new_y // 256) * self.width + (new_x // 256)

            if old_idx != new_idx and self.get_pixel(new_x // 256, new_y // 256):
                delta = abs(new_idx - old_idx)

                if delta == 1:
                    new_x = self.grain[i].x
                    self.grain[i].vx = self.bounce(self.grain[i].vx)

                elif delta == self.width:
                    new_y = self.grain[i].y
                    self.grain[i].vy = self.bounce(self.grain[i].vy)

                else:
                    if abs(self.grain[i].vx) >= abs(self.grain[i].vy):
                        if not self.get_pixel(new_x // 256, self.grain[i].y // 256):
                            new_y = self.grain[i].y
                            self.grain[i].vy = self.bounce(self.grain[i].vy)

                        else:
                            if not self.get_pixel(self.grain[i].x // 256, new_y // 256):
                                new_x = self.grain[i].x
                                self.grain[i].vx = self.bounce(self.grain[i].vx)

                            else:
                                new_x = self.grain[i].x
                                new_y = self.grain[i].y
                                self.grain[i].vx = self.bounce(self.grain[i].vx)
                                self.grain[i].vy = self.bounce(self.grain[i].vy)

                    else:
                        if not self.get_pixel(self.grain[i].x // 256, new_y // 256):
                            new_x = self.grain[i].x
                            self.grain[i].vx = self.bounce(self.grain[i].vx)

                        else:
                            if not self.get_pixel(new_x // 256, self.grain[i].y // 256):
                                new_y = self.grain[i].y
                                self.grain[i].vy = self.bounce(self.grain[i].vy)

                            else:
                                new_x = self.grain[i].x
                                new_y = self.grain[i].y
                                self.grain[i].vx = self.bounce(self.grain[i].vx)
                                self.grain[i].vy = self.bounce(self.grain[i].vy)

            self.clear_pixel(self.grain[i].x // 256, self.grain[i].y // 256)
            self.grain[i].x = new_x
            self.grain[i].y = new_y
            self.set_pixel(new_x // 256, new_y // 256)


# 定义绕X轴、Y轴、Z轴的旋转矩阵函数
def rotate_x(theta):
    return np.array([
        [1, 0, 0],
        [0, np.cos(theta), -np.sin(theta)],
        [0, np.sin(theta), np.cos(theta)]
    ])

def rotate_y(theta):
    return np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])

def rotate_z(theta):
    return np.array([
        [np.cos(theta), -np.sin(theta), 0],
        [np.sin(theta), np.cos(theta), 0],
        [0, 0, 1]
    ])

# 定义一个旋转函数，通过组合旋转矩阵实现
# def rotate_xyz(alpha, beta, gamma):
#     return rotate_z(gamma) @ rotate_y(beta) @ rotate_x(alpha)

# 定义一个三维坐标
# point = np.array([1, 0, 0])

# 定义旋转角度（弧度）
# alpha = np.radians(0)  # 绕X轴旋转30度
# beta = np.radians(-90)   # 绕Y轴旋转45度
# gamma = np.radians(60)  # 绕Z轴旋转60度

# 获取旋转矩阵
# rotation_matrix = rotate_xyz(alpha, beta, gamma)

# 进行坐标变换
# rotated_point = rotation_matrix @ point

# 打印结果
# print("Original Point:", point)
# print("Rotated Point:", rotated_point)

def main():
    # Initialize LED matrix options
    options = RGBMatrixOptions()
    options.hardware_mapping = 'adafruit-hat'
    options.rows = 16
    options.cols = 32
    options.chain_length = 1

    # Create LED matrix
    matrix = RGBMatrix(options=options)

    # Create offscreen canvas for double-buffered animation
    canvas = matrix.CreateFrameCanvas()
    width, height = canvas.width, canvas.height

    # Initialize PixelDust
    n_flakes = 100
    snow = Adafruit_PixelDust(width, height, n_flakes, 1, 8, True)
    snow.begin()
    snow.randomize()
    while True:
        # Simulate accelerometer data (replace with actual data)
        ax, ay, az = get_acce()
        accel = np.array([ax, ay, az])
        # print(accel)
        # print(f"ax: {ax}, ay: {ay}, az: {az}")
        # rotation_angle = math.radians(90)
        # new_ax = ay * math.cos(rotation_angle) - az * math.sin(rotation_angle)
        # new_az = ay * math.sin(rotation_angle) + az * math.cos(rotation_angle)

        new_accel = rotate_z(np.radians(5)) @ rotate_x(np.radians(-30)) @ rotate_y(np.radians(90)) @ accel
        # print(new_accel)

        # Iterate PixelDust and update canvas
        # snow.iterate(ax, ay, az)
        snow.iterate(new_accel[0], new_accel[1], new_accel[2])

        canvas.Clear()
        for i in range(n_flakes):
            x, y = snow.get_position(i)
            canvas.SetPixel(x, y, 255, 255, 255)

        # Swap canvas on the next vertical sync
        canvas = matrix.SwapOnVSync(canvas)
        # update_fifo(matrix, fifo_path)


if __name__ == "__main__":
    main()