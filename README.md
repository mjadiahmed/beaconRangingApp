# Beacon Distance Ranging Application

## Overview

This application is designed to read data from beacons via serial communication, parse the data, and display it in a Tkinter GUI. It tracks the Received Signal Strength Indicator (RSSI) values of beacons, updates the displayed information in real-time, and saves the data to a CSV file. Users can also edit distance and comments associated with each beacon.

## Features

- **Serial Communication:** Establishes a serial connection to receive beacon data.
- **Data Parsing:** Extracts MAC addresses and RSSI values from received packets.
- **Real-Time Updates:** Displays and updates beacon information in the GUI.
- **CSV Logging:** Saves beacon data to a CSV file for record-keeping.
- **Editable Fields:** Allows users to edit the distance and comments directly in the GUI.

## Getting Started

### Prerequisites

Make sure you have Python installed on your system. You can download it from [python.org](https://www.python.org/).

### Installation

1. Clone the repository or download the project files.
2. Install the required libraries using the following command:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Program

1. Start the application with:
    ```bash
    python BeaconSerial.py
    ```
2. In the GUI:
   - **Choose the USB port** from the dropdown menu.
   - **Click "Start Listening"** to begin scanning for beacons.
   - **Insert the distance** for each beacon by double-clicking the distance column in the table and entering the new value.
   - **Click "Save"** to store the updated data into the `distance_rssi_data.csv` file.

## Code Overview

### Serial Communication

This function starts the serial communication with the chosen port and baud rate.

```python
def start_listening():
    global ser
    port = port_combobox.get()
    baudrate = baud_combobox.get()

    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print("Starting serial communication...")
        update_rssi()
    except serial.SerialException as e:
        messagebox.showerror("Error", f"Failed to open serial port: {e}")
```