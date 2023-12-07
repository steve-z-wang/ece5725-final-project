#include "led-matrix.h"
#include <fstream>
#include <iostream>
#include <signal.h>
#include <unistd.h>

using namespace rgb_matrix;

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) { interrupt_received = true; }

void GetCurrentTime(char *buffer) {
  time_t now = time(NULL);
  struct tm *tm_struct = localtime(&now);
  strftime(buffer, 6, "%H:%M", tm_struct); // Format time as HHMM
}

int main(int argc, char *argv[]) {
  RGBMatrix::Options matrix_options;
  matrix_options.hardware_mapping = "adafruit-hat";
  matrix_options.rows = 16;
  matrix_options.cols = 32;
  matrix_options.chain_length = 3;

  rgb_matrix::RuntimeOptions runtime_opt;

  RGBMatrix *matrix = CreateMatrixFromOptions(matrix_options, runtime_opt);
  if (matrix == NULL) {
    std::cerr << "Error creating matrix." << std::endl;
    return 1;
  }

  std::ifstream fifo("/tmp/matrix_fifo", std::ios::binary);
  if (!fifo) {
    std::cerr << "Cannot open FIFO." << std::endl;
    return 1;
  }

  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  char time_str[6]; // Buffer to store the current time

  FrameCanvas *offscreen_canvas = matrix->CreateFrameCanvas();
  std::vector<uint8_t> image_data(matrix_options.rows * matrix_options.cols * matrix_options.chain_length * 3); // 3 bytes per pixel (RGB)

  while (!interrupt_received) {

    // Read the entire binary image data from the FIFO
    if (!fifo.read(reinterpret_cast<char *>(image_data.data()), image_data.size())) {
      fifo.clear();                  // Clear error flags
      fifo.close();                  // Close the stream
      fifo.open("/tmp/matrix_fifo"); // Reopen FIFO for next read
      continue;
    }

    GetCurrentTime(time_str); 
    std::cout << "Received new data at " << time_str << std::endl;

    int total_rows = matrix_options.rows * matrix_options.chain_length; // Total columns for all chained panels

    for (int y = 0; y < total_rows; ++y) {
      for (int x = 0; x < matrix_options.cols; ++x) {
        int offset = (y * matrix_options.cols + x) * 3; // RGB data offset

        int x2 = y / matrix_options.rows * matrix_options.cols + x;
        int y2 = y % matrix_options.rows; 

        offscreen_canvas->SetPixel(x2, y2, image_data[offset],
                                   image_data[offset + 1],
                                   image_data[offset + 2]);
      }
    }

    offscreen_canvas = matrix->SwapOnVSync(offscreen_canvas);
  }

  fifo.close();  // Close the stream
  delete matrix; // Cleanup
  return 0;
}
