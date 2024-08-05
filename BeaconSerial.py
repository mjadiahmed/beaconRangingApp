import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv
import numpy
import os
from datetime import datetime, timedelta

ser = None
last_rssi = None
mac_to_row = {}  # Dictionary to map MAC address to row ID in the table
updated_rows = set()  # Set to track updated rows
mac_last_seen = {}  # Dictionary to track the last time each MAC address was seen

def read_serial_data():
    global ser
    if ser and ser.in_waiting > 0:
        byte = ser.read(1)
        if byte == b'\xef':  # Start byte 1
            next_byte = ser.read(1)
            if next_byte == b'\x01':  # Start byte 2
                packet = [byte, next_byte]
                for _ in range(7):  # Read 7 more bytes (6 MAC + 1 RSSI)
                    packet.append(ser.read(1))
                packet.extend(ser.read(2))  # Read 2 bytes for CRC sum
                return packet
    return None

def parse_packet(packet):
    start_bytes = packet[:2]
    if start_bytes != [b'\xef', b'\x01']:
        raise ValueError("Invalid start bytes")

    mac_address = numpy.flip(packet[2:8])
    rssi = packet[8][0]
    if rssi > 127:
        rssi -= 256  # Convert to signed integer
    crc = packet[9:]

    return mac_address, rssi

def on_data_received():
    global last_rssi
    packet = read_serial_data()
    if packet:
        try:
            mac_address, rssi = parse_packet(packet)
            mac_address_str = ':'.join(format(b[0], '02x') for b in mac_address)
            update_table(mac_address_str, rssi)
        except ValueError as e:
            print(f"Error processing packet: {e}")

def update_table(mac_address_str, rssi):
    current_time = datetime.now()
    mac_last_seen[mac_address_str] = current_time

    if mac_address_str in mac_to_row:
        # Update existing row
        row_id = mac_to_row[mac_address_str]
        table.item(row_id, values=(mac_address_str, rssi, table.item(row_id, 'values')[2], 'Connected'))
        updated_rows.add(row_id)  # Mark this row as updated
    else:
        # Insert new row
        row_id = table.insert('', 'end', values=(mac_address_str, rssi, '', 'Connected'))
        mac_to_row[mac_address_str] = row_id
        updated_rows.add(row_id)  # Mark this row as updated

def update_rssi():
    on_data_received()

    # Update status for each row
    for mac_address, row_id in mac_to_row.items():
        last_seen = mac_last_seen.get(mac_address)
        if last_seen:
            elapsed_time = datetime.now() - last_seen
            status = 'Connected' if elapsed_time <= timedelta(seconds=10) else 'Disconnected'
            current_values = table.item(row_id, 'values')
            table.item(row_id, values=(current_values[0], current_values[1], current_values[2], status))
            # Update status color
            tags = ['connected'] if status == 'Connected' else ['disconnected']
            table.item(row_id, tags=tags)

    root.after(1000, update_rssi)  # Update every 1 second

def save_to_csv():
    file_exists = os.path.isfile('distance_rssi_data.csv')
    with open('distance_rssi_data.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # Write header if file does not exist
        if not file_exists or os.path.getsize('distance_rssi_data.csv') == 0:
            writer.writerow(['MAC Address', 'RSSI', 'Distance', 'Date', 'Time'])
        # Write data rows
        for row_id in updated_rows:
            row = table.item(row_id)['values']
            if len(row) == 4:  # Check if all columns are filled
                date_time_now = datetime.now()
                date_str = date_time_now.strftime('%Y-%m-%d')
                time_str = date_time_now.strftime('%H:%M:%S')
                writer.writerow(row[:3] + [date_str, time_str])
        # Clear the updated rows set after saving
        updated_rows.clear()

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
            table.item(selected_item, values=(current_values[0], current_values[1], new_distance, current_values[3]))
            entry.destroy()
            updated_rows.add(selected_item)  # Mark this row as updated

        entry.bind('<Return>', on_entry_validate)
        entry.bind('<FocusOut>', lambda e: entry.destroy())

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

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

# GUI code
root = tk.Tk()
root.title("Beacon Distance Ranging")  # Set the window title

# Set the favicon
root.iconbitmap('logo.ico')  # Ensure 'logo.ico' is in the same directory or provide the full path

# Apply dark mode colors
root.configure(bg='#2e2e2e')
style = ttk.Style(root)
style.theme_use('clam')
style.configure("TFrame", background='#2e2e2e')
style.configure("TLabel", background='#2e2e2e', foreground='#ffffff')
style.configure("TCombobox", background='#2e2e2e', foreground='#ffffff', fieldbackground='#2e2e2e')
style.configure("TButton", background='#444444', foreground='#ffffff')
style.configure("Treeview", background='#2e2e2e', fieldbackground='#2e2e2e', foreground='#ffffff', rowheight=25)
style.configure("Treeview.Heading", background='#444444', foreground='#ffffff')
style.map("TButton", background=[('active', '#555555')])

# Define custom styles for selected rows
style.map("Treeview", background=[('selected', '#2e2e2e')], foreground=[('selected', '#ffffff')])

# Serial Port and Baud Rate Frame
frame = ttk.Frame(root)
frame.pack(pady=10)  # Add some padding around the frame

# Serial Port Selection
port_label = ttk.Label(frame, text="Port:")
port_label.pack(side=tk.LEFT, padx=5)

ports = list_serial_ports()
port_combobox = ttk.Combobox(frame, values=ports)
port_combobox.pack(side=tk.LEFT, padx=5)

# Baud Rate Selection
baud_label = ttk.Label(frame, text="Baud Rate:")
baud_label.pack(side=tk.LEFT, padx=5)

baud_rates = ["9600", "115200"]  # Add more baud rates if needed
baud_combobox = ttk.Combobox(frame, values=baud_rates)
baud_combobox.current(1)  # Default to 115200
baud_combobox.pack(side=tk.LEFT, padx=5)

# Start Button
start_button = ttk.Button(frame, text="Start Listening", command=start_listening)
start_button.pack(side=tk.LEFT, padx=5)

# Create Table
table = ttk.Treeview(root, columns=('MAC Address', 'RSSI', 'Distance', 'Status'), show='headings')
table.heading('MAC Address', text='MAC Address')
table.heading('RSSI', text='RSSI')
table.heading('Distance', text='Distance')
table.heading('Status', text='Status')

# Modify tag colors
table.tag_configure('connected', background='#2e2e2e', foreground='#3cff00')  #  green
table.tag_configure('disconnected', background='#2e2e2e', foreground='#ff0000')  #  red

table.pack(fill=tk.BOTH, expand=True, pady=10)

# Add double-click event binding to edit distance
table.bind('<Double-1>', edit_distance)

# Save Button
save_button = ttk.Button(root, text="Save", command=save_to_csv)
save_button.pack(side=tk.LEFT, padx=5, pady=10)

root.mainloop()
