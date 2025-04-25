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
player_char = ">"
gravity = 20.0  # Acceleration due to gravity (pixels/second²)
jump_strength = -10.0  # Negative because up is lower y-values

# Game state
score = 0
game_over = False
passed_columns = set()  # Keep track of columns we've passed through

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
    global player_velocity, game_over
    if select.select([sys.stdin], [], [], 0)[0] != []:
        key = sys.stdin.read(1)
        if key == ' ':  # Space bar
            if game_over:
                reset_game()
            else:
                player_velocity = jump_strength
        # Clear any remaining input
        while select.select([sys.stdin], [], [], 0)[0] != []:
            sys.stdin.read(1)


def reset_game():
    global player_y, player_velocity, score, game_over, columns, passed_columns
    player_y = y_pixel // 2
    player_velocity = 0
    score = 0
    game_over = False
    passed_columns.clear()

    # Reset columns
    columns.clear()
    current_x = x_pixel
    for _ in range(num_columns):
        gap_start = random.randint(1, y_pixel - gap_height - 1)
        columns.append([current_x, gap_start])
        current_x += random.randint(min_spacing, max_spacing)


def check_collision():
    global game_over, score
    player_y_int = int(player_y)

    for col_x, gap_start in columns:
        if int(col_x) == player_x:
            # Check if player is in the gap
            if not (gap_start <= player_y_int < gap_start + gap_height):
                game_over = True
            # Add to score if we haven't counted this column yet
            elif col_x not in passed_columns:
                passed_columns.add(col_x)
                score += 1


def generateFrame():
    if game_over:
        return generate_game_over_screen()

    output = f"Score: {score}\n"
    output += "-" * (x_pixel + 2) + "\n"
    for i in range(y_pixel):
        output += "|"
        for j in range(x_pixel):
            if i == int(player_y) and j == player_x:
                output += player_char
                continue

            column_here = False
            for col_x, gap_start in columns:
                if int(col_x) == j:
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


def generate_game_over_screen():
    output = f"Game Over - Score: {score}\n"
    output += "-" * (x_pixel + 2) + "\n"

    # Center the game over message
    game_over_msg = "GAME OVER - Press SPACE to restart"
    padding = (x_pixel - len(game_over_msg)) // 2

    for i in range(y_pixel):
        output += "|"
        if i == y_pixel // 2:
            output += " " * padding + game_over_msg + " " * \
                (x_pixel - padding - len(game_over_msg))
        else:
            output += " " * x_pixel
        output += "|\n"
    output += "-" * (x_pixel + 2) + "\n"
    return output


def outputFrame(frame):
    # Move cursor up to the top of the game area (including score line)
    sys.stdout.write('\033[H')  # Move to top of screen
    sys.stdout.write('\033[2J')  # Clear entire screen
    sys.stdout.write(frame)
    sys.stdout.flush()


def updatePosition(delta_time):
    global player_y, player_velocity, game_over

    if game_over:
        return

    # Update player physics
    player_velocity += gravity * delta_time
    player_y += player_velocity * delta_time

    # Keep player within bounds and check for ground collision
    if player_y >= y_pixel - 1:
        player_y = y_pixel - 1
        game_over = True  # Game over when hitting the ground
    elif player_y < 0:
        player_y = 0
        player_velocity = 0

    # Update columns
    for i in range(len(columns)):
        columns[i][0] -= speed * delta_time
        if columns[i][0] < 0:
            rightmost = max(col[0] for col in columns)
            new_position = max(
                rightmost + random.randint(min_spacing, max_spacing), x_pixel)
            new_gap = random.randint(1, y_pixel - gap_height - 1)
            columns[i] = [new_position, new_gap]

    check_collision()


try:
    # Set up keyboard
    init_keyboard()

    # Clear screen and move cursor to top
    print('\033[2J\033[H', end='')  # Clear screen and move to top

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
