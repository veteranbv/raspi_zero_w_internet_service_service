# work in progress
import socket
import time
import random
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import ST7789

# Create ST7789 LCD display class for Display HAT Mini
disp = ST7789.ST7789(
    height=240,
    width=320,
    rotation=180,
    port=0,
    cs=1,
    dc=9,
    backlight=13,
    spi_speed_hz=60 * 1000 * 1000,
    offset_left=0,
    offset_top=0
)

# Initialize display.
disp.begin()

WIDTH = disp.width
HEIGHT = disp.height

# Load custom font.
font = ImageFont.truetype("/usr/share/fonts/truetype/piboto/Piboto-BoldItalic.ttf", 30)

# Clear the display to black.
img = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
draw = ImageDraw.Draw(img)

# Constants
N_SAMPLES = 48
BAR_WIDTH = 5
BAR_SPACING = 2

# Generate test data
def check_connection():
    # Randomly return True (connected) or False (not connected)
    return random.choice([True, False])

def get_speed():
    # Randomly return a speed between 1 and 100
    return random.randint(1, 100)

def seed_data():
    connection_data = np.zeros(N_SAMPLES, dtype=bool)
    speed_data = np.zeros(N_SAMPLES, dtype=int)
    for i in range(N_SAMPLES):
        connection_data[i] = check_connection()
        speed_data[i] = get_speed()
    return connection_data, speed_data

connection_data, speed_data = seed_data()

# Plotting function
def plot_data(connection_data, speed_data):
    fig, ax = plt.subplots(figsize=(WIDTH / 80, HEIGHT / 80), dpi=80)
    ax.set_xlim(0, N_SAMPLES * (BAR_WIDTH + BAR_SPACING))
    ax.set_ylim(0, 100)
    ax.set_axis_off()

    for i in range(N_SAMPLES):
        x = i * (BAR_WIDTH + BAR_SPACING)
        y = speed_data[i]
        color = "green" if connection_data[i] else "red"
        ax.bar(x, y, BAR_WIDTH, color=color)

    plt.savefig("graph.png", bbox_inches="tight")

while True:
    # Clear the display
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

    if check_connection():
        # If the device is connected to the internet, display the text in green
        draw.text((0, 0), "Wi-Fi is currently up", font=font, fill=(0, 255, 0))
        # Get the current time
        current_time = time.time()
        # Append the current time and 1 (representing up) to the connection data list
        connection_data.append((current_time, 1))
        # Plot the connection data as a bar graph
        for i, (x, y) in enumerate(connection_data):
            if y == 1:
                color = (0, 255, 0)
            else:
                color = (255, 0, 0)
            draw.rectangle((x, 50, x + bar_width, 50 + bar_height), fill=color)
    else:
        # If the device is not connected to the internet, display the text in red
        draw.text((0, 0), "Wi-Fi is currently down", font=font, fill=(255, 0, 0))
        # Get the current time
        current_time = time.time()
        # Append the current time and 0 (representing down) to the connection data list
        connection_data.append((current_time, 0))
        # Plot the connection data as a bar graph
        for i, (x, y) in enumerate(connection_data):
            if y == 1:
                color = (0, 255, 0)
            else:
                color = (255, 0, 0)
            draw.rectangle((x, 50, x + bar_width, 50 + bar_height), fill=color)

    # Write buffer to display hardware
    disp.display(img)
    time.sleep(15)
