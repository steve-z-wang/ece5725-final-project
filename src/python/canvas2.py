import time

from canvas import Canvas 
from PIL import Image
import os
class ScrollableCanvas2(Canvas):
    def __init__(self, width, height, display_width, display_height, *args, **kwargs):
        if display_width > width or display_height > height:
            raise ValueError("Display size must not exceed canvas size")

        super().__init__(width, height, *args, **kwargs)
        self.display_width = display_width
        self.display_height = display_height
        self.offset_x = 0  # Initial x offset
        self.offset_y = 0  # Initial y offset

    def move_offsets(self, dx, dy):
        """Move the offsets within the canvas bounds with wrapping."""
        self.offset_x = (self.offset_x + dx) % self.width
        self.offset_y = (self.offset_y + dy) % self.height

    def get_focused_area(self):
        """Return the wrapped image based on the current offsets."""
        wrapped_image = Image.new("RGB", (self.display_width, self.display_height), self.background_color)

        # Paste the part from the original image
        wrapped_image.paste(self.image, (-self.offset_x, -self.offset_y))

        # Wrap the remaining part from the original image
        if self.offset_x + self.display_width > self.width:
            wrap_width = self.offset_x + self.display_width - self.width
            wrap_part = self.image.crop((0, 0, wrap_width, self.height))
            wrapped_image.paste(wrap_part, (self.display_width - wrap_width, 0))

        if self.offset_y + self.display_height > self.height:
            wrap_height = self.offset_y + self.display_height - self.height
            wrap_part = self.image.crop((0, 0, self.width, wrap_height))
            wrapped_image.paste(wrap_part, (0, self.display_height - wrap_height))

        return wrapped_image