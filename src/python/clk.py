
#20,21,19,26
import RPi.GPIO as GPIO
import subprocess

def GPIO19_callback(channel):
    cmd = 'echo "19"'
    subprocess.check_output(cmd, shell=True)
    print("GPIO 19 Falling Edge Detected")

def GPIO20_callback(channel):
    cmd = 'echo "20"'
    subprocess.check_output(cmd, shell=True)
    print("GPIO 20 Falling Edge Detected")

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(19, GPIO.FALLING, callback=GPIO19_callback, bouncetime=300)
    GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(20, GPIO.FALLING, callback=GPIO20_callback, bouncetime=300)
    print("GPIO Interrupt Handling Program")
    while True:
        pass  # Do other things or add a sleep here if needed

    GPIO.cleanup()

if __name__ == "__main__":
    main()
