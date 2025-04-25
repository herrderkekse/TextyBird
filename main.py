import time
import sys
import random

x_pixel = 100
y_pixel = 20
speed = 30  # Pixels per second
min_spacing = 15  # Minimum space between columns
max_spacing = 40  # Maximum space between columns
num_columns = 0  # Number of columns
gap_height = 3  # Height of the opening in columns

# Player physics
player_x = 20  # Fixed x position
player_y = 0  # Starting y position
player_velocity = 0  # Vertical velocity
gravity = 30.0  # Acceleration due to gravity (pixels/second²)

# Initialize columns with random spacing and gap positions
# Each column is now [x_position, gap_start_y]
columns = []
current_x = x_pixel
for _ in range(num_columns):
    # Ensure gap doesn't touch edges
    gap_start = random.randint(1, y_pixel - gap_height - 1)
    columns.append([current_x, gap_start])
    current_x += random.randint(min_spacing, max_spacing)


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
            # Find rightmost column
            rightmost = max(col[0] for col in columns)
            # Ensure the new position is at least at the right edge
            new_position = max(
                rightmost + random.randint(min_spacing, max_spacing), x_pixel)
            # Generate new random gap position
            new_gap = random.randint(1, y_pixel - gap_height - 1)
            columns[i] = [new_position, new_gap]


# Print initial empty lines to allow cursor movement
print("\n" * (y_pixel + 2))

last_time = time.time()
while True:
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    updatePosition(delta_time)
    frm = generateFrame()
    outputFrame(frm)
    time.sleep(0.016)  # Cap at roughly 60 FPS
