#!/bin/bash

# Function to kill both processes
cleanup() {
    echo "Cleaning up..."
    kill -9 $PID_PYTHON $PID_LED 2>/dev/null
}

# Run the Python script in the background
python ./src/python/clockWithButtons.py &
PID_PYTHON=$!

sleep 1

# Run the LED matrix display in the background
sudo ./build/LEDMatrixMultiDisplay &
PID_LED=$!

# Trap EXIT signal to call the cleanup function
trap cleanup EXIT

# Wait for both processes to end
wait $PID_PYTHON $PID_LED
