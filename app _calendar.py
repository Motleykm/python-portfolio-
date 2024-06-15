import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
import requests
from datetime import datetime


# Function to fetch availability from the Flask server
def fetch_availability():
    date = cal.selection_get()
    hairdresser = hairdresser_var.get()
    date_str = date.strftime('%Y-%m-%d')

    response = requests.post(
        'http://127.0.0.1:5000/hairdresser_availability',
        json={'date': date_str, 'hairdresser': hairdresser}
    )

    if response.status_code == 200:
        data = response.json()
        availability = data.get('availability', [])
        availability_var.set(', '.join(availability))
    else:
        availability_var.set('Error fetching availability')


# Function to fetch and disable unavailable dates from the Flask server
def fetch_and_disable_unavailable_dates():
    hairdresser = hairdresser_var.get()

    response = requests.post(
        'http://127.0.0.1:5000/hairdresser_full_availability',
        json={'hairdresser': hairdresser}
    )

    if response.status_code == 200:
        data = response.json()
        unavailable_dates = data.get('unavailable_dates', [])
        disable_dates(unavailable_dates)
    else:
        print('Error fetching unavailable dates')


# Function to disable specific dates in the calendar
def disable_dates(dates):
    cal.calevent_remove('unavailable')  # Remove previous unavailable events
    cal.calevent_remove('available')  # Remove previous available events
    cal.calevent_remove('sunday')  # Remove previous Sunday events
    available_days = set()

    for date in dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        cal.calevent_create(date_obj, 'Unavailable', 'unavailable')

    # Disable Sundays and highlight available days
    for year in range(datetime.now().year, datetime.now().year + 2):  # Adjust year range as needed
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    date_obj = datetime(year, month, day)
                    day_name = date_obj.strftime('%A')
                    if day_name == "Sunday":
                        cal.calevent_create(date_obj, 'Sunday', 'sunday')
                    elif date_obj.strftime('%Y-%m-%d') not in dates:
                        available_days.add(date_obj.strftime('%Y-%m-%d'))
                except ValueError:
                    continue

    for available_date in available_days:
        date_obj = datetime.strptime(available_date, '%Y-%m-%d')
        cal.calevent_create(date_obj, 'Available', 'available')


# Function to handle hairdresser change
def on_hairdresser_change(event):
    fetch_and_disable_unavailable_dates()


# Create the main Tkinter window
root = tk.Tk()
root.title("Hairdresser Availability")

# Create a Calendar widget
cal = Calendar(root, selectmode='day', year=2024, month=6, day=12)
cal.pack(pady=20)

# Configure tags for styling
cal.tag_config('unavailable', background='gray', foreground='white')
cal.tag_config('available', background='violet', foreground='black')
cal.tag_config('sunday', background='white', foreground='black')

# Hairdresser selection
ttk.Label(root, text="Select Hairdresser:").pack(pady=10)
hairdresser_var = tk.StringVar()
hairdresser_combo = ttk.Combobox(root, textvariable=hairdresser_var)
hairdresser_combo['values'] = ["Jamil", "Shanice", "Cherish", "Arrinana"]
hairdresser_combo.current(0)  # Set default value
hairdresser_combo.bind("<<ComboboxSelected>>", on_hairdresser_change)
hairdresser_combo.pack(pady=10)

# Fetch availability button
fetch_btn = ttk.Button(root, text="Fetch Availability", command=fetch_availability)
fetch_btn.pack(pady=20)

# Display availability
ttk.Label(root, text="Available Times:").pack(pady=10)
availability_var = tk.StringVar()
availability_label = ttk.Label(root, textvariable=availability_var)
availability_label.pack(pady=10)

# Fetch and disable unavailable dates for the default selected hairdresser
fetch_and_disable_unavailable_dates()

# Start the Tkinter event loop
root.mainloop()
