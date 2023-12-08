#include "led-matrix.h"
#include <chrono>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <signal.h>
#include <sys/select.h>
#include <thread>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>

using namespace rgb_matrix;

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) { interrupt_received = true; }

void GetCurrentTime(char *buffer) {
  time_t now = time(NULL);
  struct tm *tm_struct = localtime(&now);
  strftime(buffer, 9, "%H:%M:%S", tm_struct); // Format time as HHMM
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

  FrameCanvas *offscreen_canvas = matrix->CreateFrameCanvas();
  std::vector<uint8_t> image_data(matrix_options.rows * matrix_options.cols *
                                  matrix_options.chain_length *
                                  3); // 3 bytes per pixel (RGB)

  int total_rows =
      matrix_options.rows *
      matrix_options.chain_length; // Total columns for all chained panels

  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  char time_str[9]; // Buffer to store the current time

  const char *fifoPath = "/tmp/matrix_fifo";

  // Check if the FIFO file already exists
  struct stat st;
  if (stat(fifoPath, &st) != 0) {
    // FIFO doesn't exist, so create it
    if (mkfifo(fifoPath, 0666) != 0) {
      std::cerr << "Failed to create FIFO: " << fifoPath << std::endl;
      return 1;
    }
  }

  // Now open the FIFO
  int fifo_fd = open(fifoPath, O_RDONLY | O_NONBLOCK);
  if (fifo_fd < 0) {
    std::cerr << "Cannot open FIFO." << std::endl;
    return 1;
  }

  while (!interrupt_received) {

    fd_set fds;
    FD_ZERO(&fds);
    FD_SET(fifo_fd, &fds);

    struct timeval timeout;
    timeout.tv_sec = 1; // 1 second timeout
    timeout.tv_usec = 0;

    // Wait for data to be available on the FIFO
    int ret = select(fifo_fd + 1, &fds, NULL, NULL, &timeout);

    if (ret > 0) {

      ssize_t bytes_read = read(fifo_fd, image_data.data(), image_data.size());

      if (bytes_read > 0) {
        GetCurrentTime(time_str);
        std::cout << "LEDMatrixMultiDisplay : received new data at " << time_str << std::endl;

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

      } else {
        close(fifo_fd);
        fifo_fd = open(fifoPath, O_RDONLY | O_NONBLOCK);
        if (fifo_fd < 0) {
          std::cerr << "Failed to reopen FIFO." << std::endl;
          break;
        }
      }
    }
  }

  close(fifo_fd);
  delete matrix; // Cleanup
  return 0;
}
