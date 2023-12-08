from PIL import Image
import os

class Canvas:
    def __init__(self, width, height, fifo_path="/tmp/matrix_fifo", background_color=(0, 0, 0)):
        self.width = width
        self.height = height
        self.background_color = background_color
        self.image = Image.new("RGB", (width, height), background_color)
        self.fifo_path = fifo_path

        self.snapshots = []

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
            
    def start_fall(self, state):
        while self.fall_one_pixel(state):
            pass
        
    def fall_one_pixel(self, state):
        # save current image to snapshots
        self.snapshots.append(self.image.copy())
        # print("add len = ", len(self.snapshots))

        exist_fallable = False

        # vertical down mode
        if state == 'vertical_down':
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
        elif state == 'vertical_up':
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

    def replay_one_snapshot(self):
        # print("len = ", len(self.snapshots))
        if len(self.snapshots) != 0:
            img = self.snapshots.pop()
            self.image.paste(img)
            return True
        return False

    # replay fall one pixel
    def replay_one_pixel(self):
        if len(self.fall_record_stack) == 0:
            return False
        snapshot = self.fall_record_stack.pop()

        if self.prev_state == "vertical_down":
            for layer in snapshot:
                for x, y in layer:
                    self.image.putpixel((x, y), self.image.getpixel((x + 1, y)))
                    self.image.putpixel((x + 1, y), self.background_color)

        elif self.prev_state == "vertical_up":
            for layer in snapshot:
                for x, y in layer:
                    self.image.putpixel((x, y), self.image.getpixel((x - 1, y)))
                    self.image.putpixel((x - 1, y), self.background_color)
        else:
            for layer in snapshot:
                for x, y in layer:
                    self.image.putpixel((x, y), self.image.getpixel((x, y + 1)))
                    self.image.putpixel((x, y + 1), self.background_color)
        return True
    

class ScrollableCanvas(Canvas):
    def __init__(self, width, height, display_width, display_height, *args, **kwargs):

        if display_width > width or display_height > height:
            raise ValueError("Display size must not exceed canvas size")

        super().__init__(width, height, *args, **kwargs)
        self.display_width = display_width
        self.display_height = display_height
        self.focus_x = 0  # Initial focus point
        self.focus_y = 0
        
    def set_focus(self, focus_x, focus_y):
        """Move the focus point within the canvas bounds, wrapping around if necessary."""
        self.focus_x = focus_x % self.width
        self.focus_y = focus_y % self.height

    def move_focus(self, dx, dy):
        """Move the focus point within the canvas bounds, wrapping around if necessary."""
        self.focus_x = (self.focus_x + dx) % self.width
        self.focus_y = (self.focus_y + dy) % self.height

    def get_focused_area(self):
        """Return the cropped image area based on the current focus, with wrapping."""
        focused_area = Image.new("RGB", (self.display_width, self.display_height), self.background_color)

        for x_offset in range(0, self.display_width):
            for y_offset in range(0, self.display_height):
                src_x = (self.focus_x + x_offset) % self.width
                src_y = (self.focus_y + y_offset) % self.height
                focused_area.putpixel((x_offset, y_offset), self.image.getpixel((src_x, src_y)))

        return focused_area

    def show(self):
        """Show the current focused area of the canvas."""
        focused_area = self.get_focused_area()
        focused_area.show()

    def save(self, filename):
        """Save the current focused area of the canvas to a file."""
        focused_area = self.get_focused_area()
        focused_area.save(filename)

    def update_fifo(self):
        """Serialize the focused area of the image as binary data and write it to the FIFO."""
        focused_area = self.get_focused_area()
        image_binary = focused_area.tobytes()
        with open(self.fifo_path, 'wb') as fifo:
            fifo.write(image_binary)
