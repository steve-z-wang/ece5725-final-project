from PIL import Image
import os
from imu_pose import Pose

class Canvas:
    def __init__(self, width, height, fifo_path="/tmp/matrix_fifo", background_color=(0, 0, 0)):
        self.width = width
        self.height = height
        self.background_color = background_color
        self.image = Image.new("RGB", (width, height), background_color)
        self.fifo_path = fifo_path
        try:
            if not os.path.exists(fifo_path):
                os.mkfifo(fifo_path)
        except Exception as e:
            print(f"Error creating FIFO: {e}")

    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.image.putpixel((x, y), color)
        else:
            print(f"Pixel coordinates out of bounds: ({x}, {y})")
    
    def start_fall(self, state):
        while self.fall_one_pixel(state):
            pass
        
    def fall_one_pixel(self, state):
        exist_fallable = False
        # (dx, dy) = (1, 0) or (0, 1) or (0, -1)

        # vertical down mode
        if state == Pose.VERTICAL_DOWN:
            for x in range(self.width - 2, -1, -1):
                for y in range(self.height):
                    # find non-empty pixel
                    val = self.image.getpixel((x, y))
                    if val != self.background_color:
                        # check downward pixel
                        down_val = self.image.getpixel((x + 1, y))
                        if down_val == self.background_color:
                            # fall down one pixel
                            self.image.putpixel((x + 1, y), val)
                            self.image.putpixel((x, y), self.background_color)
                            exist_fallable = True

        # vertical up mode
        elif state == Pose.VERTICAL_UP:
            for x in range(1, self.width):
                for y in range(self.height):
                    # find non-empty pixel
                    val = self.image.getpixel((x, y))
                    if val != self.background_color:
                        # check downward pixel
                        down_val = self.image.getpixel((x - 1, y))
                        if down_val == self.background_color:
                            # fall down one pixel
                            self.image.putpixel((x - 1, y), val)
                            self.image.putpixel((x, y), self.background_color)
                            exist_fallable = True

        else: # horizontal mode
            for y in range(self.height - 2, -1, -1):
                for x in range(self.witdh):
                    # find non-empty pixel
                    val = self.image.getpixel((x, y))
                    if val != self.background_color:
                        # check downward pixel
                        down_val = self.image.getpixel((x, y + 1))
                        if down_val == self.background_color:
                            # fall down one pixel
                            self.image.putpixel((x, y + 1), val)
                            self.image.putpixel((x, y), self.background_color)
                            exist_fallable = True

        return exist_fallable
    

    def clear(self):
        """Clear the canvas by setting all pixels to the specified background color."""
        self.image = Image.new("RGB", (self.width, self.height), self.background_color)

    def save(self, filename):
        try:
            self.image.save(filename)
        except Exception as e:
            print(f"Error saving file: {e}")

    def show(self):
        self.image.show()

    def load_image(self, filepath, mode='resize'):
        """Load an image from the given file path and set it as the current image."""
        if not os.path.exists(filepath):
            print("File not found")
            return

        try:
            loaded_image = Image.open(filepath)
        except Exception as e:
            print(f"Error loading image: {e}")
            return

        if mode == 'resize':
            resized_image = loaded_image.resize((self.width, self.height))
            self.image = resized_image
        elif mode == 'pixel_by_pixel':
            self.clear()  # Clear the canvas before loading new image
            min_width, min_height = min(self.width, loaded_image.width), min(self.height, loaded_image.height)
            self.image.paste(loaded_image.crop((0, 0, min_width, min_height)), (0, 0))
        else:
            print("Invalid mode selected")

    def update_fifo(self):
        try:
            image_binary = self.image.tobytes()
            with open(self.fifo_path, 'wb') as fifo:
                fifo.write(image_binary)
        except Exception as e:
            print(f"Error updating FIFO: {e}")