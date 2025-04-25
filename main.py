import time
import sys
import random
import select
import termios
import tty

x_pixel = 100
y_pixel = 20
speed = 30  # Pixels per second
min_spacing = 15  # Minimum space between columns
max_spacing = 40  # Maximum space between columns
num_columns = 4  # Number of columns
gap_height = 3  # Height of the opening in columns

# Player physics
player_x = 20  # Fixed x position
player_y = y_pixel // 2  # Starting y position
player_velocity = 0  # Vertical velocity
gravity = 20.0  # Acceleration due to gravity (pixels/second²)
jump_strength = -10.0  # Negative because up is lower y-values

# Initialize columns with random spacing and gap positions
columns = []
current_x = x_pixel
for _ in range(num_columns):
    gap_start = random.randint(1, y_pixel - gap_height - 1)
    columns.append([current_x, gap_start])
    current_x += random.randint(min_spacing, max_spacing)

# Terminal settings for non-blocking input
old_settings = termios.tcgetattr(sys.stdin)


def init_keyboard():
    tty.setcbreak(sys.stdin.fileno())


def restore_keyboard():
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def check_keyboard():
    global player_velocity
    # Check if there's input waiting (timeout of 0 makes it non-blocking)
    if select.select([sys.stdin], [], [], 0)[0] != []:
        key = sys.stdin.read(1)
        if key == ' ':  # Space bar
            player_velocity = jump_strength
        # Clear any remaining input
        while select.select([sys.stdin], [], [], 0)[0] != []:
            sys.stdin.read(1)


def generateFrame():
    output = "-" * (x_pixel + 2) + "\n"
    for i in range(y_pixel):
        output += "|"
        for j in range(x_pixel):
            # Draw player
            if i == int(player_y) and j == player_x:
                output += "P"
                continue

            # Check if any column is at this x position
            column_here = False
            for col_x, gap_start in columns:
                if int(col_x) == j:
                    # Draw space if we're in the gap, H otherwise
                    if gap_start <= i < gap_start + gap_height:
                        output += " "
                    else:
                        output += "H"
                    column_here = True
                    break
            if not column_here:
                output += " "
        output += "|\n"
    output += "-" * (x_pixel + 2) + "\n"
    return output


def outputFrame(frame):
    sys.stdout.write('\033[A' * (y_pixel + 2))  # Move cursor up
    sys.stdout.write(frame)
    sys.stdout.flush()


def updatePosition(delta_time):
    global player_y, player_velocity

    # Update player physics
    player_velocity += gravity * delta_time
    player_y += player_velocity * delta_time

    # Keep player within bounds
    if player_y >= y_pixel - 1:
        player_y = y_pixel - 1
        player_velocity = 0
    elif player_y < 0:
        player_y = 0
        player_velocity = 0

    # Update columns
    for i in range(len(columns)):
        columns[i][0] -= speed * delta_time
        if columns[i][0] < 0:  # Reset position when reaching left edge
            rightmost = max(col[0] for col in columns)
            new_position = max(
                rightmost + random.randint(min_spacing, max_spacing), x_pixel)
            new_gap = random.randint(1, y_pixel - gap_height - 1)
            columns[i] = [new_position, new_gap]


try:
    # Set up keyboard
    init_keyboard()

    # Print initial empty lines to allow cursor movement
    print("\n" * (y_pixel + 2))

    last_time = time.time()
    while True:
        current_time = time.time()
        delta_time = current_time - last_time
        last_time = current_time

        check_keyboard()  # Check for space bar press
        updatePosition(delta_time)
        frm = generateFrame()
        outputFrame(frm)
        time.sleep(0.016)  # Cap at roughly 60 FPS

finally:
    # Restore terminal settings
    restore_keyboard()
