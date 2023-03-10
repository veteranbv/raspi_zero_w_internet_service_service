# Internet Status Display

This project displays the current internet status on a Display Hat Mini 2.0, using a Raspberry Pi Zero W. The primary code is written in Python 3, but is ran via a service file that is executed on boot.

## Prerequisites

- Raspberry Pi Zero W (tested with Raspbian Bullseye)
- Display Hat Mini 2.0
- Python 3
- The libraries listed in the installation section below

## Installation

1. Follow the instructions at [Pimoroni's Display Hat Mini](https://github.com/pimoroni/displayhatmini-python) to install the Display Hat Mini Python Libraries.
2. Clone the repository or download the files.
3. Install the required libraries:

    ```bash
    sudo apt update
    sudo apt install python3-rpi.gpio python3-spidev python3-pip python3-pil python3-numpy
    sudo raspi-config nonint do_spi 0
    sudo pip3 install Pillow
    sudo pip3 install st7789
    pip3 install displayhatmini
    ```

4. Copy the files to the Raspberry Pi Zero W.

    ```bash
    internet_status.py in /home/pi/
    internet_status.service in /etc/systemd/system/
    ```

5. Enable the service:

    ```bash
   sudo systemctl enable internet-status.service
   sudo systemctl start internet-status.service
    ```

## Voila

The Display Hat Mini should now display the current internet status. If the internet is connected, the display will show a green sentence stating that the Wi-Fi is up and if the internet is not connected, the display will show a red sentence stating that the Wi-Fi is down.

<p align="center">
  <img src="https://github.com/veteranbv/raspi_zero_w_internet_service_service/blob/46ae5225b7b44de5194becf87704e6d44908cae8/WiFi-is-Up_lowres.jpeg">
</p>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
