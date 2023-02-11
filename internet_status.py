# Library used to check internet connection and display the status on a Display HAT Mini 2.0 using a Raspberry Pi Zero W

import socket
import time
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

def check_connection():
    try:
        # Try to connect to Google's server
        host = socket.gethostbyname("www.google.com")
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        # If connection fails, return False
        return False

while True:
    # Clear the display
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

    if check_connection():
        # If the device is connected to the internet, display the text in green
        draw.text((0, 0), "Wi-Fi is currently up", font=font, fill=(0, 255, 0))
    else:
        # If the device is not connected to the internet, display the text in red
        draw.text((0, 0), "Wi-Fi is currently down", font=font, fill=(255, 0, 0))

    # Write buffer to display hardware
    disp.display(img)
    time.sleep(15)