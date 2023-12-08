import RPi.GPIO as GPIO
import time

# Define your pin numbers
pin1 = 24
pin2 = 25
pin3 = 19
pin4 = 20

# Callback functions for each button
def callback_button1(channel):
    print("Button 1 pressed!")

def callback_button2(channel):
    print("Button 2 pressed!")

def callback_button3(channel):
    print("Button 3 pressed!")

def callback_button4(channel):
    print("Button 4 pressed!")

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pin2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pin3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pin4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Assign callback functions
GPIO.add_event_detect(pin1, GPIO.FALLING, callback=callback_button1, bouncetime=200)
GPIO.add_event_detect(pin2, GPIO.FALLING, callback=callback_button2, bouncetime=200)
GPIO.add_event_detect(pin3, GPIO.FALLING, callback=callback_button3, bouncetime=200)
GPIO.add_event_detect(pin4, GPIO.FALLING, callback=callback_button4, bouncetime=200)

# Keep the program running
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
