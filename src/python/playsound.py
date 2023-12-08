import subprocess

# Define the command to be executed
command = ["aplay", "-D", "plughw:1,0", "src/statics/alarm_sound1.wav"]

# Run the command five times in a loop
for _ in range(5):
    subprocess.run(command)