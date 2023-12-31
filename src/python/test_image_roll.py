import time
from canvas import ScrollableCanvas
from PIL import Image

fifo_path = "/tmp/matrix_fifo"
def get_image_size(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return width, height
    except Exception as e:
        print(f"Error: {e}")
        return None

size=get_image_size('../statics/1.jpg')
if size:
    print(f"Image size: {size[0]} x {size[1]} pixels")

canvas = ScrollableCanvas(size[0],size[1],32, 3 *  16)  # Clear the canvas

canvas.load_image('../statics/1.jpg', mode='pixel_by_pixel')
i = 0
# while True:
#     canvas.move_offsets(10,10)
#     canvas.update_fifo()
#     print("image sent")
#     time.sleep(0.5)

while True:

    print(i)
    i+=1
    canvas.move_focus(1,1)
    canvas.update_fifo()
    print("image sent")
    time.sleep(0.5)