# Beacon Distance Ranging Application

## Overview

This application is designed to read data from beacons via serial communication, parse the data, and display it in a Tkinter GUI. It tracks the Received Signal Strength Indicator (RSSI) values of beacons, updates the displayed information in real-time, and saves the data to a CSV file. Users can also edit distance and comments associated with each beacon.

![image](https://github.com/user-attachments/assets/f9a137d0-5c1a-4715-af2a-e3591a1e2d64)

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

### Real-Time Updates

Updates the status of each beacon and refreshes the GUI display.

```python
def update_rssi():
    on_data_received()

    for mac_address, row_id in mac_to_row.items():
        last_seen = mac_last_seen.get(mac_address)
        if last_seen:
            elapsed_time = datetime.now() - last_seen
            status = 'Connected' if elapsed_time <= timedelta(seconds=10) else 'Disconnected'
            current_values = table.item(row_id, 'values')
            table.item(row_id, values=(current_values[0], current_values[1], current_values[2], current_values[3], status))
            tags = ['connected'] if status == 'Connected' else ['disconnected']
            table.item(row_id, tags=tags)

    root.after(1000, update_rssi)
```



### Saving Data to CSV
Saves the updated beacon data to a CSV file.

```python
def save_to_csv():
    file_exists = os.path.isfile('distance_rssi_data.csv')
    with open('distance_rssi_data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists or os.path.getsize('distance_rssi_data.csv') == 0:
            writer.writerow(['MAC Address', 'RSSI', 'Distance', 'Comment', 'Date', 'Time'])
        for row_id in updated_rows:
            row = table.item(row_id)['values']
            if len(row) == 5:
                date_time_now = datetime.now()
                date_str = date_time_now.strftime('%Y-%m-%d')
                time_str = date_time_now.strftime('%H:%M:%S')
                writer.writerow(row[:4] + [date_str, time_str])
        updated_rows.clear()

```

### Editing Distance and Comments
Allows users to edit the distance and comments in the table.

```python
def edit_distance(event):
    selected_item = table.selection()[0]
    column = table.identify_column(event.x)
    if column == '#3':  # Distance column
        entry = ttk.Entry(root)
        entry.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())
        entry.insert(0, table.item(selected_item, 'values')[2])
        entry.focus()

        def on_entry_validate(event):
            new_distance = entry.get()
            current_values = table.item(selected_item, 'values')
            table.item(selected_item, values=(current_values[0], current_values[1], new_distance, current_values[3], current_values[4]))
            entry.destroy()
            updated_rows.add(selected_item)

        entry.bind('<Return>', on_entry_validate)
        entry.bind('<FocusOut>', lambda e: entry.destroy())
    
    elif column == '#4':  # Comment column
        entry = ttk.Entry(root)
        entry.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())
        entry.insert(0, table.item(selected_item, 'values')[3])
        entry.focus()

        def on_entry_validate(event):
            new_comment = entry.get()
            current_values = table.item(selected_item, 'values')
            table.item(selected_item, values=(current_values[0], current_values[1], current_values[2], new_comment, current_values[4]))
            entry.destroy()
            updated_rows.add(selected_item)

        entry.bind('<Return>', on_entry_validate)
        entry.bind('<FocusOut>', lambda e: entry.destroy())

```