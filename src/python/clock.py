import time
import os


fifo_path = "/tmp/time_fifo"
blink_state = True

while True:
    current_time = time.strftime("%H:%M")
    
    # Toggle blink state
    if blink_state:
        blinking_time = current_time.replace(":", " ")
    else:
        blinking_time = current_time
    
    with open(fifo_path, 'w') as fifo:
        fifo.write(blinking_time)
    
    # Toggle blink state for the next iteration
    blink_state = not blink_state
    
    time.sleep(1)  # Update every second



