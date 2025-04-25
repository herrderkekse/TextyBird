import time
import sys

x_pixel = 100
y_pixel = 20


def generateFrame():
    output = "-" * (x_pixel + 2) + "\n"
    for i in range(y_pixel):
        output += "|"
        for j in range(x_pixel):
            output += " "
        output += "|\n"
    output += "-" * (x_pixel + 2) + "\n"
    return output


def outputFrame(frame):
    sys.stdout.write('\033[A' * (y_pixel + 2))  # Move cursor up
    sys.stdout.write(frame)
    sys.stdout.flush()


# Print initial empty lines to allow cursor movement
print("\n" * (y_pixel + 2))  # Match the number of lines in your frame

while True:
    frm = generateFrame()
    outputFrame(frm)
    time.sleep(0.1)
