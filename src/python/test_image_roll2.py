import time

from canvas import ScrollableCanvas

fifo_path = "/tmp/matrix_fifo"

canvas = ScrollableCanvas(32, 3 *  16, 32, 3 * 16, fifo_path)  # Clear the canvas

canvas.load_image('/home/pi/final-project/src/statics/sun_moon.jpg', mode='resize')
canvas.update_fifo()
    
while True: 
    
    canvas.move_focus(0, 1)
    canvas.update_fifo()
    
    time.sleep(0.1)
