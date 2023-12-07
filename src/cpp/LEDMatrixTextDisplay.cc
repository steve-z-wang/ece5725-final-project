#include "include/customFont.h" // Include your custom font
#include "led-matrix.h"

#include <fstream>
#include <iostream>
#include <signal.h>
#include <unistd.h>

using namespace rgb_matrix; // Corrected namespace usage

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) { interrupt_received = true; }

// Function to display a character from the custom font
void DisplayCharacter(FrameCanvas *canvas, const DigitData &digitData,
                      int start_x, int start_y) {
  for (int y = 0; y < digitData.height; ++y) {
    for (int x = 0; x < digitData.width; ++x) {
      if (digitData.bitmap[y] & (1 << (digitData.width - 1 - x))) {
        if ((start_x + x) < canvas->width() &&
            (start_y + y) < canvas->height()) {
          canvas->SetPixel(start_x + x, start_y + y, 155, 155, 155);
        }
      }
    }
  }
}

// Function to display a string
void DisplayString(FrameCanvas *canvas, const char *str, int start_x,
                   int start_y) {
  int x = start_x;

  for (int i = 0; str[i] != '\0'; ++i) {
    DigitData character;

    if (str[i] == ':') {
      character = customFont[10]; // Colon
    } else if (str[i] == ' ') {
      character = customFont[11];
    } else {
      character = customFont[str[i] - '0']; // Numeric digit
    }

    DisplayCharacter(canvas, character, x, start_y);
    x += character.width + 1;
  }
}

void GetCurrentTime(char *buffer) {
  time_t now = time(NULL);
  struct tm *tm_struct = localtime(&now);
  strftime(buffer, 6, "%H:%M", tm_struct); // Format time as HHMM
}

int main(int argc, char *argv[]) {
  RGBMatrix::Options matrix_options;
  matrix_options.hardware_mapping = "regular"; // or e.g. "adafruit-hat"
  matrix_options.rows = 32;
  matrix_options.chain_length = 1;
  matrix_options.parallel = 1;

  rgb_matrix::RuntimeOptions runtime_opt;
  RGBMatrix *matrix =
      RGBMatrix::CreateFromFlags(&argc, &argv, &matrix_options, &runtime_opt);
  if (matrix == NULL) {
    return 1;
  }

  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  FrameCanvas *offscreen_canvas = matrix->CreateFrameCanvas();

  std::ifstream fifo_stream("/tmp/time_fifo");

  while (!interrupt_received) {
    char time_str[6]; // Buffer to store the current time

    if (!fifo_stream.read(time_str, 5)) {
      fifo_stream.clear();                // Clear error flags
      fifo_stream.close();                // Close the stream
      fifo_stream.open("/tmp/time_fifo"); // Reopen FIFO for next read
      continue;
    }

    time_str[5] = '\0'; // Null-terminate the string

    std::cout << "Received new data: " << time_str << std::endl;

    offscreen_canvas->Clear();
    DisplayString(offscreen_canvas, time_str, 1,
                  0); // Draw on the offscreen canvas
    offscreen_canvas =
        matrix->SwapOnVSync(offscreen_canvas); // Swap the offscreen canvas
  }

  fifo_stream.close(); // Close the stream
  delete matrix;       // Clean up
  return 0;
}
