# Define compiler and flags
CXX = g++
CXXFLAGS = -Wall -g
INCLUDES = -Isrc/cpp/include -Ilib/rpi-rgb-led-matrix/include

# Libraries to link against
LIBS = -Llib/rpi-rgb-led-matrix/lib -l:librgbmatrix.a -lpthread 

# Define target
TARGET = LEDMatrixMultiDisplay

# Build directory
BUILD_DIR = build

# Source and object files
SRC = src/cpp/LEDMatrixMultiDisplay.cc
OBJ = $(SRC:src/cpp/%.cc=$(BUILD_DIR)/%.o)

# Default target
all: $(BUILD_DIR) $(TARGET)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Rule to link the object file to the target
$(TARGET): $(OBJ)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $(BUILD_DIR)/$(TARGET) $(OBJ) $(LIBS)

# Rule to compile the source file to an object file
$(BUILD_DIR)/%.o: src/cpp/%.cc
	$(CXX) $(CXXFLAGS) $(INCLUDES) -c $< -o $@

# Clean target
clean:
	rm -rf $(BUILD_DIR)

# Phony targets
.PHONY: all clean $(BUILD_DIR)
