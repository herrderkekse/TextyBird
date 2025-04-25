import time
import sys
import random
import select
import termios
import tty
import os

x_pixel = 100
y_pixel = 20
speed = 40  # Pixels per second
min_spacing = 15  # Minimum space between columns
max_spacing = 40  # Maximum space between columns
num_columns = 4  # Number of columns
gap_height = 8  # Height of the opening in columns

# Player physics
player_x = 20  # Fixed x position
player_y = y_pixel // 2  # Starting y position
player_velocity = 0  # Vertical velocity
player_char = "(0)>"  # Changed from ">" to "0>"
gravity = 20.0  # Acceleration due to gravity (pixels/second²)
jump_strength = -10.0  # Negative because up is lower y-values

# Game state
score = 0
game_over = False
passed_columns = set()  # Keep track of columns we've passed through

# Highscore functionality
HIGHSCORE_FILE = "highscore.txt"
highscore = 0


def load_highscore():
    global highscore
    try:
        if os.path.exists(HIGHSCORE_FILE):
            with open(HIGHSCORE_FILE, 'r') as f:
                highscore = int(f.read().strip())
    except:
        highscore = 0


def save_highscore():
    global highscore, score
    if score > highscore:
        highscore = score
        try:
            with open(HIGHSCORE_FILE, 'w') as f:
                f.write(str(highscore))
        except:
            pass


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
    passed_columns = set()  # Change to store column indices instead of x positions

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

    for i, (col_x, gap_start) in enumerate(columns):
        # Score when passing the column (using the column index instead of x position)
        if i not in passed_columns and col_x < player_x:
            # Check if player was in the gap when passing
            if gap_start <= player_y_int < gap_start + gap_height:
                passed_columns.add(i)
                score += 1

        # Collision detection for all positions the player character occupies
        if any(int(col_x) == player_x + offset for offset in range(len(player_char))) and \
           not (gap_start <= player_y_int < gap_start + gap_height):
            game_over = True
            save_highscore()  # Save highscore when game ends


def generateFrame():
    if game_over:
        return generate_game_over_screen()

    output = f"Score: {score} | Highscore: {highscore}\n"
    output += "-" * (x_pixel + 2) + "\n"
    for i in range(y_pixel):
        output += "|"
        j = 0
        while j < x_pixel:
            if i == int(player_y) and j == player_x:
                output += player_char
                j += len(player_char)  # Skip the width of the player character
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
            j += 1
        output += "|\n"
    output += "-" * (x_pixel + 2) + "\n"
    return output


def generate_game_over_screen():
    output = f"Game Over - Score: {score} | Highscore: {highscore}\n"
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
    global player_y, player_velocity, game_over, passed_columns

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
            # Remove this column's index from passed_columns when recycling it
            passed_columns.discard(i)

    check_collision()


try:
    # Set up keyboard
    init_keyboard()

    # Load highscore at game start
    load_highscore()

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
