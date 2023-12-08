import time
import board
import digitalio
import adafruit_lis3dh

i2c = board.I2C()
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c)
# lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)

while True:
    if lis3dh.shake(shake_threshold=15):
        print("Shaken!")

# lis3dh.set_tap(1, 30)
# while True:
#     if lis3dh.tapped:
#         print("Tapped!")
#         time.sleep(0.01)