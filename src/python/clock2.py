from canvas import Canvas 
import time 

def load_custom_font(file_name):
    with open(file_name, 'r') as file:
        content = file.readlines()

    custom_font = {}
    current_char = None
    current_bitmap = []

    for line in content:
        line = line.strip()
        if line.startswith('"'):  # New character
            if current_char is not None:
                # Calculate the width of the first line in the bitmap
                width = 6 if current_char.isdigit() else 4
                custom_font[current_char] = {'bitmap': current_bitmap, 'width': width}
            current_char = line.strip('"')
            current_bitmap = []
        elif line:
            # Convert binary string to an integer representation
            current_bitmap.append(int(line, 2))

    # Add the last character to the dictionary
    if current_char is not None:
        width = 6 if current_char.isdigit() else 4
        custom_font[current_char] = {'bitmap': current_bitmap, 'width': width}

    return custom_font

def draw_text_on_canvas(canvas, text, custom_font, start_x=0, start_y=0, color=(64, 20, 0)):
    x = start_x
    y = start_y

    canvas.clear()

    for char in text:
        if char in custom_font:
            char_data = custom_font[char]
            char_bitmap = char_data['bitmap']
            char_width = char_data['width']

            for row in char_bitmap:
                for col in range(char_width):
                    if row & (1 << (char_width - 1 - col)):
                        canvas.set_pixel(x + col, y, color)

                y += 1
            x += char_width + 1  # Move to the next character position
            y = start_y          # Reset y to the starting row

        if x >= canvas.width:
            break  # Stop if we run out of space on the canvas


fifo_path = "/tmp/matrix_fifo"
custom_font = load_custom_font('../statics/custom_font.txt')
canvas = Canvas(32, 16, fifo_path)  # Clear the canvas

blink_state = True

while True:

    current_time = time.strftime("%H:%M")
    

    # Toggle blink state
    if blink_state:
        blinking_time = current_time.replace(":", " ")
    else:
        blinking_time = current_time
    
    draw_text_on_canvas(canvas, blinking_time, custom_font, color=(165, 83, 0))

    # Write to FIFO
    canvas.update_fifo()

    
    print(blinking_time)

    # Toggle blink state for the next iteration
    blink_state = not blink_state
    
    time.sleep(1)  # Update every second