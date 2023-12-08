import time

from canvas import Canvas 

fifo_path = "/tmp/matrix_fifo"

canvas = Canvas(32, 3 *  16, fifo_path)  # Clear the canvas

canvas.load_image('../statics/beautiful.jpg', mode='resize')

canvas.update_fifo()
print("image sent")
