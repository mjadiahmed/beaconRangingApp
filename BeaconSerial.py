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
mac_to_row = {}
updated_rows = set()
mac_last_seen = {}

def read_serial_data():
    global ser
    if ser and ser.in_waiting > 0:
        byte = ser.read(1)
        if byte == b'\xef':
            next_byte = ser.read(1)
            if next_byte == b'\x01':
                packet = [byte, next_byte]
                for _ in range(7):
                    packet.append(ser.read(1))
                packet.extend(ser.read(2))
                return packet
    return None

def parse_packet(packet):
    start_bytes = packet[:2]
    if start_bytes != [b'\xef', b'\x01']:
        raise ValueError("Invalid start bytes")

    mac_address = numpy.flip(packet[2:8])
    rssi = packet[8][0]
    if rssi > 127:
        rssi -= 256
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
        row_id = mac_to_row[mac_address_str]
        table.item(row_id, values=(mac_address_str, rssi, table.item(row_id, 'values')[2], table.item(row_id, 'values')[3], 'Connected'))
        updated_rows.add(row_id)
    else:
        row_id = table.insert('', 'end', values=(mac_address_str, rssi, '', '', 'Connected'))
        mac_to_row[mac_address_str] = row_id
        updated_rows.add(row_id)

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

def edit_distance(event):
    selected_item = table.selection()[0]
    column = table.identify_column(event.x)
    if column == '#3':  # Distance column
        entry = ttk.Entry(root, font=("Arial", 20))
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
        entry = ttk.Entry(root, font=("Arial", 20))
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

root = tk.Tk()
root.title("Beacon Distance Ranging")

root.iconbitmap('logo.ico')

root.configure(bg='#2e2e2e')
style = ttk.Style(root)
style.theme_use('clam')
style.configure("TFrame", background='#2e2e2e')
style.configure("TLabel", background='#2e2e2e', foreground='#ffffff', font=("Arial", 20))
style.configure("TCombobox", background='#2e2e2e', foreground='#ffffff', fieldbackground='#2e2e2e', font=("Arial", 20))
style.configure("TButton", background='#444444', foreground='#ffffff', font=("Arial", 20))
style.configure("Treeview", background='#2e2e2e', fieldbackground='#2e2e2e', foreground='#ffffff', rowheight=35, font=("Arial", 20))
style.configure("Treeview.Heading", background='#444444', foreground='#ffffff', font=("Arial", 20))
style.map("TButton", background=[('active', '#555555')])
style.map("Treeview", background=[('selected', '#2e2e2e')], foreground=[('selected', '#ffffff')])

frame = ttk.Frame(root)
frame.pack(pady=10)

port_label = ttk.Label(frame, text="Port:")
port_label.pack(side=tk.LEFT, padx=5)

ports = list_serial_ports()
port_combobox = ttk.Combobox(frame, values=ports)
port_combobox.pack(side=tk.LEFT, padx=5)

baud_label = ttk.Label(frame, text="Baud Rate:")
baud_label.pack(side=tk.LEFT, padx=5)

baud_rates = ["9600", "115200"]
baud_combobox = ttk.Combobox(frame, values=baud_rates)
baud_combobox.current(1)
baud_combobox.pack(side=tk.LEFT, padx=5)

start_button = ttk.Button(frame, text="Start Listening", command=start_listening)
start_button.pack(side=tk.LEFT, padx=5)

table = ttk.Treeview(root, columns=('MAC Address', 'RSSI', 'Distance', 'Comment', 'Status'), show='headings')
table.heading('MAC Address', text='MAC Address')
table.heading('RSSI', text='RSSI')
table.heading('Distance', text='Distance')
table.heading('Comment', text='Comment')
table.heading('Status', text='Status')

table.tag_configure('connected', background='#2e2e2e', foreground='#3cff00')
table.tag_configure('disconnected', background='#2e2e2e', foreground='#ff0000')

table.pack(fill=tk.BOTH, expand=True, pady=10)

table.bind('<Double-1>', edit_distance)

save_button = ttk.Button(root, text="Save", command=save_to_csv)
save_button.pack(side=tk.LEFT, padx=5, pady=10)

root.mainloop()
