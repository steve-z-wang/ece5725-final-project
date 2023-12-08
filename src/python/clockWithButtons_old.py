from canvas import Canvas, ScrollableCanvas
import time
import os
import RPi.GPIO as GPIO
import os
import threading
import subprocess
from imu_pose import get_pose

# functions for display


def load_custom_font(file_name):
    with open(file_name, "r") as file:
        content = file.readlines()

    custom_font = {}
    current_char = None
    current_bitmap = []

    for line in content:
        line = line.strip()
        if line.startswith('"'):  # New character
            if current_char is not None:
                # Calculate the width of the first line in the bitmap
                custom_font[current_char] = {"bitmap": current_bitmap, "width": width}
            current_char = line.strip('"')
            current_bitmap = []
        elif line:
            # Convert binary string to an integer representation
            width = len(line)
            current_bitmap.append(int(line, 2))

    # Add the last character to the dictionary
    if current_char is not None:
        custom_font[current_char] = {"bitmap": current_bitmap, "width": width}

    return custom_font


def draw_text_on_canvas(
    canvas, text, custom_font, start_x=0, start_y=0, color=(0, 0, 0)
):
    x = start_x
    y = start_y

    canvas.clear()

    for char in text:
        if char in custom_font:
            char_data = custom_font[char]
            char_bitmap = char_data["bitmap"]
            char_width = char_data["width"]

            for row in char_bitmap:
                for col in range(char_width):
                    if row & (1 << (char_width - 1 - col)):
                        canvas.set_pixel(x + col, y, color)

                y += 1
            x += char_width + 1  # Move to the next character position
            y = start_y  # Reset y to the starting row

        if x >= canvas.width:
            break  # Stop if we run out of space on the canvas


def display_text(text):
    global setting, state, canvas, custom_font

    start_y = state["display-panel"] * setting["panel-rows"]
    draw_text_on_canvas(
        canvas, text, custom_font, start_y=start_y, color=setting["clock_font_color"]
    )
    canvas.update_fifo()

    print(f'{file_name}: display test "{text}" on panel {state["display-panel"]}')


# callback functions for controls


def start_new_thread(func):
    global all_threads

    new_thread = threading.Thread(target=func)
    new_thread.start()
    all_threads.append(new_thread)


def left_button_callback(channel):
    global state, alarm, setting_blink_state

    print(f"{file_name}: left button pressed")

    if state["setting_alarm"]:
        if not state["setting_minute"]:
            alarm["hour"] = (alarm["hour"] + 1) % 24
        else:
            alarm["minute"] = (alarm["minute"] + 1) % 60
        display_text(f"{alarm['hour']:02}:{alarm['minute']:02}")
        setting_blink_state = False


def right_button_callback(channel):
    global state

    print(f"{file_name}: middle button pressed")

    if not state["setting_alarm"]:
        state["setting_alarm"] = True
        start_new_thread(set_alarm)
    elif state["setting_alarm"] and not state["setting_minute"]:
        state["setting_minute"] = True
    elif state["setting_alarm"] and state["setting_minute"]:
        state["setting_alarm"] = False
        state["setting_minute"] = False


# fonctions for different states


def set_alarm():
    global state, alarm, setting_blink_state

    print(f"{file_name}: set_alarm thread begins")

    setting_blink_state = True
    while state["setting_alarm"] and not state["setting_minute"]:
        blinking_time = (
            f"__:{alarm['minute']:02}"
            if setting_blink_state
            else f"{alarm['hour']:02}:{alarm['minute']:02}"
        )
        display_text(blinking_time)
        setting_blink_state = not setting_blink_state
        time.sleep(0.5)

    setting_blink_state = True
    while state["setting_alarm"] and state["setting_minute"]:
        blinking_time = (
            f"{alarm['hour']:02}:__"
            if setting_blink_state
            else f"{alarm['hour']:02}:{alarm['minute']:02}"
        )
        display_text(blinking_time)
        setting_blink_state = not setting_blink_state
        time.sleep(0.5)

    print(f"{file_name}: set_alarm thread ends")


def alarm_effect():
    global state, alarm
    print(f"{file_name}: alarm_effect thread begins")
    # Define the command to be executed
    command = ["aplay", "-D", "plughw:1,0", "src/statics/alarm_sound1.wav"]
    while not state["alarm_on"]:
        # Execute the command
        subprocess.run(command)
    print(f"{file_name}: alarm_effect thread ends")


# Initilization

full_path = __file__
file_name = os.path.basename(full_path)

# Pins
left_button_pin = 19
right_button_pin = 20

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(left_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(right_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(
    left_button_pin, GPIO.FALLING, callback=left_button_callback, bouncetime=200
)
GPIO.add_event_detect(
    right_button_pin, GPIO.FALLING, callback=right_button_callback, bouncetime=200
)

fifo_path = "/tmp/matrix_fifo"

setting = {
    "clock_background_color": (0, 0, 0),
    "clock_font_color": (255, 200, 100),
    "panel-cols": 32,
    "panel-rows": 16,
    "num_of_panels": 3,
}
state = {
    "setting_alarm": False,
    "setting_minute": False,
    "is_horizontal": True,
    "alarm_on": False,
    "display-panel": 0,
}
alarm = {"hour": 5, "minute": 56}

# start imu
all_threads = []

# set up canvas
custom_font = load_custom_font("./src/statics/custom_font.txt")
canvas_width, canvas_height = (
    setting["panel-cols"],
    setting["panel-rows"] * setting["num_of_panels"],
)
canvas = ScrollableCanvas(
    canvas_width,
    canvas_height,
    canvas_width,
    canvas_height,
    fifo_path,
    background_color=setting["clock_background_color"],
)  # Clear the canvas

clock_blink_state = False
while True:
    
    # get position info
    pos = get_pose()
    if pos == 2:
        state['display-panel'] = 0
    elif pos == 3:
        state['display-panel'] = 1
    elif pos == 4:
        state['display-panel'] = 2
        
        
    # clock
    if not state["setting_alarm"] and state["is_horizontal"]:
        current_time = time.strftime("%H:%M")

        # check if is the alarm time
        alarm_time = f"{alarm['hour']:02}:{alarm['minute']:02}"

        if not state["alarm_on"] and current_time == alarm_time:
            state["alarm_on"] = True
            start_new_thread(alarm_effect)

        # display time
        blinking_time = (
            current_time.replace(":", " ") if clock_blink_state else current_time
        )
        display_text(blinking_time)
        clock_blink_state = not clock_blink_state

    time.sleep(1)  # Update every second

    # check alarm
