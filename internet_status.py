import socket
import time
import subprocess
import psutil
import RPi.GPIO as GPIO
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import ST7789
import datetime
from io import BytesIO
import tempfile

SAMPLE_INTERVAL_SECONDS = 300  # 5 minutes
SAMPLES_PER_HOUR = int(3600 / SAMPLE_INTERVAL_SECONDS)
TIME_INTERVALS = [1, 4, 12, 24, 168, 720]  # Hours: 1, 4, 12, 24, Week: 168, Month: 720
current_time_interval_index = 0
current_color_theme_index = 0
current_screen = "default"

# Color themes
COLOR_THEMES = [
    {"bg": (0, 0, 0), "text": (255, 255, 255), "connected": (0, 255, 0), "disconnected": (255, 0, 0)},
    {"bg": (255, 255, 255), "text": (0, 0, 0), "connected": (0, 128, 0), "disconnected": (128, 0, 0)},
    {"bg": (50, 50, 50), "text": (255, 255, 255), "connected": (0, 255, 255), "disconnected": (255, 127, 80)},
    {"bg": (240, 240, 240), "text": (0, 0, 0), "connected": (0, 150, 136), "disconnected": (244, 67, 54)},
    {"bg": (0, 51, 102), "text": (255, 255, 255), "connected": (255, 153, 0), "disconnected": (204, 0, 0)},
    {"bg": (245, 245, 245), "text": (30, 30, 30), "connected": (77, 182, 172), "disconnected": (239, 83, 80)},
    {"bg": (255, 255, 255), "text": (54, 57, 63), "connected": (67, 181, 129), "disconnected": (214, 48, 49)},
    # Add more color themes here
]

# Button GPIO Pins
BUTTON_A = 5
BUTTON_B = 6
BUTTON_X = 16
BUTTON_Y = 24

class Sample:
    def __init__(self, timestamp, signal_strength):
        self.timestamp = timestamp
        self.signal_strength = signal_strength

samples = []

def add_sample(signal_strength):
    timestamp = datetime.datetime.now()
    samples.append(Sample(timestamp, signal_strength))

def update_wifi_status_data():
    global samples, refresh_display
    current_time = datetime.datetime.now()

    # Remove samples older than the longest interval (1 month)
    samples = [sample for sample in samples if (current_time - sample.timestamp).total_seconds() <= TIME_INTERVALS[-1] * 3600]

    # Add a new sample
    network_info = gather_network_info()
    add_sample(int(network_info["signal_strength"]))  # Ensure signal_strength is an integer

    refresh_display = True

def calculate_average_signal_strength(interval_hours):
    global samples
    current_time = datetime.datetime.now()
    interval_start_time = current_time - datetime.timedelta(hours=interval_hours)

    interval_samples = [sample for sample in samples if sample.timestamp >= interval_start_time]

    if not interval_samples:
        return 0

    sum_signal_strength = sum(sample.signal_strength for sample in interval_samples)
    return sum_signal_strength / len(interval_samples)

WIDTH = 320
HEIGHT = 240

def init_display():
    disp = ST7789.ST7789(
        height=HEIGHT,
        width=WIDTH,
        rotation=180,
        port=0,
        cs=1,
        dc=9,
        backlight=13,
        spi_speed_hz=60 * 1000 * 1000,
        offset_left=0,
        offset_top=0
    )
    disp.begin()
    return disp

def check_connection():
    try:
        host = socket.gethostbyname("www.google.com")
        s = socket.create_connection((host, 80), 2)
        return True
    except:
        return False

def gather_network_info():
    network_info = {"ip": None, "ssid": None, "signal_strength": None}

    try:
        for iface in psutil.net_if_addrs():
            if iface.startswith("wlan"):
                for addr in psutil.net_if_addrs()[iface]:
                    if addr.family == socket.AF_INET:
                        network_info["ip"] = addr.address

                result = subprocess.run(["iwconfig", iface], capture_output=True, text=True)
                for line in result.stdout.split("\n"):
                    if "ESSID" in line:
                        try:
                            network_info["ssid"] = line.split('ESSID:"')[1].split('"')[0]
                        except IndexError:
                            network_info["ssid"] = "Unknown"
                    if "Link Quality" in line:
                        network_info["signal_strength"] = line.split("Signal level=")[1].split(" ")[0]
    except Exception as e:
        print(f"Error gathering network info: {e}")

    return network_info

def display_wifi_status(disp, connected, network_info):
    color_theme = COLOR_THEMES[current_color_theme_index]
    img = Image.new("RGB", (WIDTH, HEIGHT), color_theme["bg"])
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/piboto/Piboto-BoldItalic.ttf", 30)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/piboto/Piboto-BoldItalic.ttf", 12)
    except IOError:
        font = ImageFont.load_default().font_variant(size=30)
        font_small = ImageFont.load_default().font_variant(size=12)

    if connected:
        draw.text((0, 0), "Wi-Fi is currently up", font=font, fill=color_theme["connected"])
    else:
        draw.text((0, 0), "Wi-Fi is currently down", font=font, fill=color_theme["disconnected"])

    if current_screen == "default":
        draw_bar_chart(samples, img, draw)
    elif current_screen == "network_info":
        draw.text((0, 60), f"IP: {network_info['ip']}", font=font, fill=color_theme["text"])
        draw.text((0, 100), f"SSID: {network_info['ssid']}", font=font, fill=color_theme["text"])
        draw.text((0, 140), f"Signal: {network_info['signal_strength']} dBm", font=font, fill=color_theme["text"])

    disp.display(img)

# Button callbacks
def button_a_callback(channel):
    global refresh_display, current_screen, show_graph
    print("Button A pressed")
    current_screen = "network_info" if current_screen == "default" else "default"
    refresh_display = True
    if current_screen == "default":
        show_graph = True
    time.sleep(0.2)

def button_b_callback(channel):
    global current_color_theme_index, refresh_display
    print("Button B pressed")
    current_color_theme_index = (current_color_theme_index + 1) % len(COLOR_THEMES)
    refresh_display = True
    time.sleep(0.2)

def button_x_callback(channel):
    global current_time_interval_index, refresh_display, show_graph, current_screen
    print("Button X pressed")
    current_time_interval_index = (current_time_interval_index + 1) % len(TIME_INTERVALS)
    if current_screen == "network_info":
        current_screen = "default"
    show_graph = True
    refresh_display = True
    time.sleep(0.2)

def button_y_callback(channel):
    global refresh_display
    print("Button Y pressed")
    refresh_display = True
    time.sleep(0.2)

def setup_buttons():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_X, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_Y, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(BUTTON_A, GPIO.FALLING, callback=button_a_callback, bouncetime=500)
    GPIO.add_event_detect(BUTTON_B, GPIO.FALLING, callback=button_b_callback, bouncetime=500)
    GPIO.add_event_detect(BUTTON_X, GPIO.FALLING, callback=button_x_callback, bouncetime=500)
    GPIO.add_event_detect(BUTTON_Y, GPIO.FALLING, callback=button_y_callback, bouncetime=500)

# Calculate the available space between the text lines
text_line_1_y = 33
text_line_2_y = HEIGHT - 15
available_space = text_line_2_y - text_line_1_y

# Update the draw_bar_chart function
def draw_bar_chart(data, img, draw):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        create_graph()
        plt.savefig(temp_file.name, format='png', dpi=80)  # Add dpi parameter to control the size
        graph_img = Image.open(temp_file.name)

        # Calculate the graph height (leave some margin, e.g., 30 pixels)
        graph_height = available_space - 25

        # Resize the graph to the desired height
        graph_img = graph_img.resize((WIDTH, graph_height))

        # Calculate the Y-coordinate for the graph to be centered vertically
        graph_y = text_line_1_y + (available_space - graph_height) // 2

        # Position the graph between two lines of text
        img.paste(graph_img, (0, graph_y))

        plt.clf()  # Clear the figure to avoid memory leaks

def create_graph():
    plt.figure(figsize=(4, 3))  # Adjust the size here
    time_interval = TIME_INTERVALS[current_time_interval_index]
    current_time = datetime.datetime.now()
    interval_start_time = current_time - datetime.timedelta(hours=time_interval)
    filtered_samples = [sample for sample in samples if sample.timestamp >= interval_start_time]

    x = [sample.timestamp for sample in filtered_samples]  # Updated x-axis to represent time
    y = [sample.signal_strength for sample in filtered_samples]
    plt.bar(x, y)
    plt.xlabel("Time")
    plt.ylabel("Signal Strength (dBm)")
    plt.title(f"Wi-Fi Signal Strength over {time_interval} hours")

def main():
    global img, draw, refresh_display, show_graph
    refresh_display = False
    show_graph = True

    last_update = time.time()

    disp = init_display()

    # Display the Wi-Fi status initially
    network_info = gather_network_info()
    try:
        connected = check_connection()
    except Exception as e:
        print(f"Error checking connection: {e}")
        connected = False
    display_wifi_status(disp, connected, network_info)

    # Setup GPIO buttons
    setup_buttons()

    while True:
        if refresh_display:
            print(f"Refreshing display - current_screen: {current_screen}")
            if current_screen == "default":
                try:
                    connected = check_connection()
                except Exception as e:
                    print(f"Error checking connection: {e}")
                    connected = False
                network_info = gather_network_info()
                display_wifi_status(disp, connected, network_info)
            elif current_screen == "network_info":
                network_info = gather_network_info()
                display_wifi_status(disp, connected, network_info)

            refresh_display = False

        time.sleep(0.1)

        if time.time() - last_update > 60 * 60:  # 1 hour
            update_wifi_status_data()
            last_update = time.time()  # Update the last_update variable


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        GPIO.cleanup()
