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


def right_button_callback(channel):
    global state

    print(f"{file_name}: right button pressed")

    if not state["setting_alarm"]:
        state["setting_alarm"] = True
        start_new_thread(set_alarm)

    elif not state["setting_minute"]:
        state["setting_minute"] = True

    else:
        state["setting_alarm"] = False
        state["setting_minute"] = False


def left_button_callback(channel):
    global state, setting_blink_state

    print(f"{file_name}: left button pressed")

    if not state["setting_alarm"]:
        return

    alarm_time = state["alarm_time"]
    hour_str, minute_str = alarm_time.split(":")
    hour, minute = int(hour_str), int(minute_str)

    if state["setting_minute"]:
        minute = (minute + 5) % 60
    else:
        hour = (hour + 1) % 24

    new_alarm_time = f"{hour:02}:{minute:02}"
    state["alarm_time"] = new_alarm_time
    display_text(new_alarm_time)
    setting_blink_state = False


def red_button_callback(channel):

    global state

    if not state['rolling_image_active']:
        state['rolling_image_active'] = True
        start_new_thread(roll_image)
    else:
        state['rolling_image_active'] = False


def green_button_callback(channel):


    pass

# functions for different states


def roll_image():
    global state 

    canvas.load_image('/home/pi/final-project/src/statics/show.jpg', mode='resize')
    canvas.update_fifo()
    
    while state['rolling_image_active']: 
    
        canvas.move_focus(0, 1)
        canvas.update_fifo()
        time.sleep(0.1)

    canvas.set_focus(0, 0)

def set_alarm():
    global state, alarm, setting_blink_state

    print(f"{file_name}: set_alarm thread begins")

    if state["alarm_time"] == None:
        state["alarm_time"] = "00:00"

    setting_blink_state = True
    while state["setting_alarm"]:
        alarm_time = state["alarm_time"]

        if not state["setting_minute"]:
            blinking_time = (
                "__:" + alarm_time.split(":")[1] if setting_blink_state else alarm_time
            )
        else:
            blinking_time = (
                alarm_time.split(":")[0] + ":__" if setting_blink_state else alarm_time
            )

        display_text(blinking_time)
        setting_blink_state = not setting_blink_state
        time.sleep(0.5)

    print(f"{file_name}: set_alarm thread ends")


def raise_alarm_effect():
    global state, alarm
    print(f"{file_name}: alarm starts")

    state["alarm_time"] = None
    command = ["aplay", "-D", "plughw:1,0", "src/statics/alarm_sound1.wav"]
    while state["alarm_on"]:
        subprocess.run(command)
    print(f"{file_name}: alarm ends")


def update_transition_offset():
    if (
        state["display-panel"] < state["transition_target"]
        or state["display-panel"] == 2
        and state["transition_target"] == 0
    ):
        state["panel_transition_y_offset"] += setting["panel-rows"]
    else:
        state["panel_transition_y_offset"] -= setting["panel-rows"]


def start_panel_transition():
    global state, setting, canvas
    print(f"{file_name}: start panel transition")

    # alarm turn off
    state["alarm_on"] = False

    target = 0
    if (
        state["transition_target"] - state["display-panel"] == 1
        or state["display-panel"] == 2
        and state["transition_target"] == 0
    ):
        target -= setting["panel-rows"]
    else:
        target += setting["panel-rows"]

    offset = 0
    while offset != target:
        if offset < target:
            offset += 1
        else:
            offset -= 1

        canvas.set_focus(0, offset)

        display_text(state["cur_time_display_text"])
        time.sleep(0.1)

    canvas.set_focus(0, 0)
    state["display-panel"] = state["transition_target"]
    state["in_panel_transition"] = False

    print(f"{file_name}: panel transition ends")


def start_fall():
    global canvas

    if len(canvas.snapshots) != 0:
        return

    print(f"{file_name}: start fall")

    # alarm turn off
    state["alarm_on"] = False

    fall_done = False

    while not state["is_horizontal"] and not state["setting_alarm"]:
        if fall_done:
            continue
        if state["vertical_up"]:
            while canvas.fall_one_pixel("vertical_up"):
                canvas.update_fifo()
                time.sleep(0.1)
            fall_done = True
        else:
            while canvas.fall_one_pixel("vertical_down"):
                canvas.update_fifo()
                time.sleep(0.1)
            fall_done = True
        
        
def fall_backward():
    global canvas
    print(f"{file_name}: start fall backward")
    while state["is_horizontal"] and canvas.replay_one_snapshot():
        canvas.update_fifo()
        time.sleep(0.1)
    state["in_fall_backward_animation"] = False

# Initilization

full_path = __file__
file_name = os.path.basename(full_path)

# Pins
red_button_pin = 24
green_button_pin = 25
blue_button_pin = 19
yellow_button_pin = 20

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(red_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(green_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(blue_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(yellow_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(
    blue_button_pin, GPIO.FALLING, callback=left_button_callback, bouncetime=200
)
GPIO.add_event_detect(
    yellow_button_pin, GPIO.FALLING, callback=right_button_callback, bouncetime=200
)

GPIO.add_event_detect(
    red_button_pin, GPIO.FALLING, callback=red_button_callback, bouncetime=200
)
GPIO.add_event_detect(
    green_button_pin, GPIO.FALLING, callback=green_button_callback, bouncetime=200
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
    "alarm_on": False,
    "alarm_time": None,
    # "alarm_time": '00:58',
    "setting_alarm": False,
    "setting_minute": False,
    "is_horizontal": True,
    "vertical_up": None,
    "in_fall_backward_animation": False, 
    "display-panel": 1,
    "transition_target": 1,
    "in_panel_transition": False,
    "cur_time_display_text": None,
    "rolling_image_active": False
}
pos2panel_map = {2: 1, 3: 0, 4: 2}

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

prev_state = None
clock_blink_state = False
while True:
    
    # check position
    pos = get_pose()
    if pos == 0 or pos == 1:
        state["is_horizontal"] = False
        state["vertical_up"] = True if pos == 1 else False
    elif pos == 2 or pos == 3 or pos == 4:
        state["is_horizontal"] = True
        state["transition_target"] = pos2panel_map[pos]
    else:
        pass
    

    # update time display buffer
    current_time = time.strftime("%H:%M")
    blinking_time = (
        current_time.replace(":", " ") if clock_blink_state else current_time
    )
    clock_blink_state = not clock_blink_state
    state["cur_time_display_text"] = blinking_time

    # setting alarm mode
    if state["setting_alarm"]:
        pass

    elif state["rolling_image_active"]:
        pass
    
    # vertical mode
    elif not state["is_horizontal"]:
        start_new_thread(start_fall)

    # clock mode
    else:
        
        # check alarm
        if state["alarm_time"] == current_time and not state["alarm_on"]:
            state["alarm_on"] = True
            start_new_thread(raise_alarm_effect)
            
        # # fallback animation
        if prev_state is not None and not prev_state['is_horizontal']: 
            state["in_fall_backward_animation"] = True
            start_new_thread(fall_backward)

        # if moved then start panel transition
        if (
            state["display-panel"] != state["transition_target"]
            and not state["in_panel_transition"]
        ):
            state["in_panel_transition"] = True
            start_new_thread(start_panel_transition)

        # else just display panel
        else:
            display_text(blinking_time)
            
    prev_state = state.copy()
    time.sleep(1)  # Update every second
