import time
import os
import RPi.GPIO as GPIO

fifo_path = "/tmp/time_fifo"
blink_state = True

class ClockWithButtons:
    def __init__(self, fifo_path, left_button_pin, middle_button_pin, right_button_pin):
        self.fifo_path = fifo_path
        self.left_button_pin = left_button_pin
        self.middle_button_pin = middle_button_pin
        self.right_button_pin = right_button_pin

        self.blink_state = True
        self.hour = 0
        self.minute = 0
        self.setting_time = False
        self.setting_minute = False

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.left_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.middle_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.right_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Set up button callbacks
        GPIO.add_event_detect(self.left_button_pin, GPIO.FALLING, callback=self.left_button_callback, bouncetime=300)
        GPIO.add_event_detect(self.middle_button_pin, GPIO.FALLING, callback=self.middle_button_callback, bouncetime=300)
        GPIO.add_event_detect(self.right_button_pin, GPIO.FALLING, callback=self.right_button_callback, bouncetime=300)

    def set_time(self, hour, minute):
        new_time = f"{hour:02d}:{minute:02d}"
        with open(self.fifo_path, 'w') as fifo:
            fifo.write(new_time)

    def toggle_blink_state(self):
        if self.blink_state:
            blinking_time = time.strftime("%H:%M").replace(":", " ")
        else:
            blinking_time = time.strftime("%H:%M")
        with open(self.fifo_path, 'w') as fifo:
            fifo.write(blinking_time)
        self.blink_state = not self.blink_state

    def enter_time_setting_mode(self):
        self.setting_time = True
        while self.setting_time:
            time.sleep(1)

    def enter_minute_setting_mode(self):
        self.setting_minute = True
        while self.setting_minute:
            time.sleep(1)

    def left_button_callback(self, channel):
        if self.setting_time:
            self.hour = (self.hour - 1) % 24
        elif self.setting_minute:
            self.minute = (self.minute - 1) % 60
        self.set_time(self.hour, self.minute)

    def middle_button_callback(self, channel):
        if not self.setting_time:
            self.toggle_blink_state()
        else:
            self.enter_minute_setting_mode()
        time.sleep(0.5)  # Debounce

    def right_button_callback(self, channel):
        if self.setting_time:
            self.hour = (self.hour + 1) % 24
        elif self.setting_minute:
            self.minute = (self.minute + 1) % 60
        self.set_time(self.hour, self.minute)

    def run(self):
        while True:
            if not self.setting_time:
                self.toggle_blink_state()
            time.sleep(1)

if __name__ == "__main__":
    fifo_path = "/tmp/time_fifo"
    left_button_pin = 17
    middle_button_pin = 18
    right_button_pin = 19

    clock = ClockWithButtons(fifo_path, left_button_pin, middle_button_pin, right_button_pin)
    clock.run()