#!/bin/bash

# Change directory to the location of your Python script
cd ~/final-project/src/python

# Run the Python script
python clock.py & 

# Change directory to the location of your C++ program
cd ~/final-project

# Run the C++ program with sudo privileges
sudo ./LEDMatrixTextDisplay --led-rows=16 --led-cols=32 --led-gpio-mapping=adafruit-hat
