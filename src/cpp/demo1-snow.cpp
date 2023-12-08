/*!
 * @file demo1-snow.cpp
 *
 * Simple example for Adafruit_PixelDust on Raspberry Pi.
 * REQUIRES rpi-rgb-led-matrix LIBRARY!
 * I2C MUST BE ENABLED using raspi-config!
 *
 */

#ifndef ARDUINO // Arduino IDE sometimes aggressively builds subfolders

#include "Adafruit_PixelDust.h"
#include "led-matrix-c.h"
// #include "lis3dh.h"
#include <signal.h>
#include <fstream>
#include <iostream>

#define N_FLAKES 900 ///< Number of snowflakes on 64x64 matrix

struct RGBLedMatrix *matrix = NULL;
// Adafruit_LIS3DH lis3dh;
volatile bool running = true;
int nFlakes = N_FLAKES; // Runtime flake count (adapts to res)

// Signal handler allows matrix to be properly deinitialized.
int sig[] = {SIGHUP,  SIGINT, SIGQUIT, SIGABRT,
             SIGKILL, SIGBUS, SIGSEGV, SIGTERM};
#define N_SIGNALS (int)(sizeof sig / sizeof sig[0])

void irqHandler(int dummy) {
  if (matrix) {
    led_matrix_delete(matrix);
    matrix = NULL;
  }
  for (int i = 0; i < N_SIGNALS; i++)
    signal(sig[i], NULL);
  running = false;
}

int main(int argc, char **argv) {
  
   // Open the named pipe (FIFO) for reading
    std::ifstream fifo("/tmp/accel_fifo");

    if (!fifo.is_open()) {
        std::cerr << "Error opening the FIFO.\n";
        return 1;
    }
    
  struct RGBLedMatrixOptions options;
  struct LedCanvas *canvas;
  int width, height, i, xx, yy, zz;
  Adafruit_PixelDust *snow = NULL;
  dimension_t x, y;

  for (i = 0; i < N_SIGNALS; i++)
    signal(sig[i], irqHandler); // ASAP!

  // Initialize LED matrix defaults
  memset(&options, 0, sizeof(options));
  matrix_options.hardware_mapping = "adafruit-hat";
  options.rows = 16;
  options.cols = 32;
  options.chain_length = 1;

  // Parse command line input.  --led-help lists options!
  matrix = led_matrix_create_from_options(&options, &argc, &argv);
  if (matrix == NULL)
    return 1;

  // Create offscreen canvas for double-buffered animation
  canvas = led_matrix_create_offscreen_canvas(matrix);
  led_canvas_get_size(canvas, &width, &height);
  fprintf(stderr, "Size: %dx%d. Hardware gpio mapping: %s\n", width, height,
          options.hardware_mapping);

  if (width < 64)
    nFlakes /= 2; // Adjust snow count
  if (height < 64)
    nFlakes /= 2; // for smaller matrices

  snow = new Adafruit_PixelDust(width, height, nFlakes, 1, 64, true);
  if (!snow->begin()) {
    puts("PixelDust init failed");
    return 2;
  }

  snow->randomize(); // Initialize random snowflake positions

  while (running) {
    // Read accelerometer data from the FIFO
        std::string line;
        std::getline(fifo, line);

        // Parse the accelerometer data
        std::istringstream iss(line);
        if (!(iss >> xx >> yy >> zz)) {
            std::cerr << "Error parsing accelerometer data.\n";
            continue;
        }
    snow->iterate(-xx, -yy, zz);

    // Erase canvas and draw new snowflake positions
    led_canvas_clear(canvas);
    for (i = 0; i < nFlakes; i++) {
      snow->getPosition(i, &x, &y);
      led_canvas_set_pixel(canvas, x, y, 255, 255, 255);
    }

    // Update matrix contents on next vertical sync
    // and provide a new canvas for the next frame.
    canvas = led_matrix_swap_on_vsync(matrix, canvas);
  }

  return 0;
}

#endif // !ARDUINO
