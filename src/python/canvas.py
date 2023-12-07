from PIL import Image
import os

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

class ScrollableCanvas(Canvas):
    def __init__(self, width, height, display_width, display_height, *args, **kwargs):

        if display_width > width or display_height > height:
            raise ValueError("Display size must not exceed canvas size")

        super().__init__(width, height, *args, **kwargs)
        self.display_width = display_width
        self.display_height = display_height
        self.focus_x = 0  # Initial focus point
        self.focus_y = 0

    def move_focus(self, dx, dy):
        """Move the focus point within the canvas bounds."""
                # Calculate the new focus position
        new_focus_x = max(0, min(self.focus_x + dx, self.width - self.display_width))
        new_focus_y = max(0, min(self.focus_y + dy, self.height - self.display_height))

        # Check if the new focus is within the bounds of the canvas
        if new_focus_x != self.focus_x or new_focus_y != self.focus_y:
            self.focus_x, self.focus_y = new_focus_x, new_focus_y
        else:
            raise ValueError("Cannot move focus further in the given direction")

    def get_focused_area(self):
        """Return the cropped image area based on the current focus, handling wrapping."""
        end_x = self.focus_x + self.display_width
        end_y = self.focus_y + self.display_height

        if end_x <= self.width and end_y <= self.height:
            # No wrapping, regular crop
            return self.image.crop((self.focus_x, self.focus_y, end_x, end_y))
        else:
            # Create a new image for the wrapped area
            focused_area = Image.new("RGB", (self.display_width, self.display_height), self.background_color)

            # Crop and paste the part from the end of the canvas
            part_end_canvas = self.image.crop((self.focus_x, self.focus_y, self.width, self.height))
            focused_area.paste(part_end_canvas, (0, 0))

            # Crop and paste the part from the beginning of the canvas
            if end_x > self.width:
                part_begin_canvas = self.image.crop((0, 0, end_x - self.width, end_y))
                focused_area.paste(part_begin_canvas, (self.width - self.focus_x, 0))
            if end_y > self.height:
                part_begin_canvas = self.image.crop((0, 0, end_x, end_y - self.height))
                focused_area.paste(part_begin_canvas, (0, self.height - self.focus_y))

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
