import threading
import subprocess
import logging

def run_command(cmd):
    try:
        logging.info(f"Starting command: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        logging.info("Command finished successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred: {e}")


logging.basicConfig(level=logging.INFO)

# Clock command
command = "sudo ./lib/rpi-rgb-led-matrix/examples-api-use/clock  --led-chain=1 -f ./lib/rpi-rgb-led-matrix/fonts/6x13B.bdf --led-rows=16 --led-cols=32 --led-gpio-mapping=adafruit-hat"

# Create a thread to run the command
command_thread = threading.Thread(target=run_command, args=(command,))

# Start the thread
command_thread.start()

# Optionally wait for the thread to finish
command_thread.join() 