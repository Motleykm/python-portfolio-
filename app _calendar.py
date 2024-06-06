import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import requests
from datetime import datetime

 Flask server URL
FLASK_SERVER_URL = "http://127.0.0.1:5000"


 #Get fully booked dates from Flask server
def fetch_fully_booked_dates():
    try:
        response = requests.get(f"{FLASK_SERVER_URL}/get_fully_booked_dates")
        if response.status_code == 200:
           return response.json()
        else:
           messagebox.showerror("Error", "Failed to fetch fully booked dates.")
            return {}
    except requests.RequestException as e:
       messagebox.showerror("Error", f"Failed to fetch fully booked dates: {e}")
       return {}


# Book an appointment
def book_appointment():
    date_str = cal.get_date()
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Error", "Invalid date format.")
        return

    hairdresser = hairdresser_var.get()
    time = time_var.get()
    services = service_entry.get()

    if not services:
        messagebox.showerror("Error", "Please enter the services.")
        return

    data = {
       "day": date.strftime("%A"),
        "time": time,
        "hairdresser": hairdresser,
        "services": services,
        "email": "customer@example.com"  # Example email
    }
    try:
        response = requests.post(f"{FLASK_SERVER_URL}/submit_appointment", data=data)
        if response.status_code == 200:
           messagebox.showinfo("Success", "Appointment booked successfully.")
        else:
            messagebox.showerror("Error", "Failed to book appointment.")
    except requests.RequestException as e:
       messagebox.showerror("Error", f"Failed to book appointment: {e}")


 Initialize Tkinter
root = tk.Tk()
root.title("Appointment Booking")
root.configure(bg="#2e2e2e")

# Fetch fully booked dates
fully_booked_dates = fetch_fully_booked_dates()

# Create the style for the calendar and other widgets
style = ttk.Style(root)
style.configure('TLabel', font=('Helvetica', 12), foreground='white', background='#2e2e2e')
style.configure('TButton', font=('Helvetica', 12, 'bold'), foreground='black', background='#4CAF50')
style.configure('TEntry', font=('Helvetica', 12), foreground='black', background='#ffffff')

# Hairdresser selection
hairdresser_label = ttk.Label(root, text="Select Hairdresser:")
hairdresser_label.pack(pady=(20, 5))
hairdresser_var = tk.StringVar(root)
hairdresser_var.set("Shanice")  # Default value
hairdresser_menu = ttk.OptionMenu(root, hairdresser_var, "Shanice", *fully_booked_dates.keys())
"""hairdresser_menu.pack(pady=(0, 20))

# Calendar widget with custom styles
cal = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd', year=2024, month=6, day=1,
               background='violet', foreground='white', selectbackground='red', selectforeground='yellow')
cal.pack(pady=20)


# Disable fully booked dates
def disable_fully_booked_dates(*args):
    cal.calevent_remove('booked')
    hairdresser = hairdresser_var.get()
    booked_dates = fully_booked_dates.get(hairdresser, [])
    for date in booked_dates:
        try:
            date_obj = datetime.strptime(date, '%A').replace(year=2024)  # Assuming the dates are from the current year
            cal.calevent_create(date_obj, 'Fully Booked', 'booked')
        except ValueError:
            pass
    cal.tag_config('booked', background='grey', foreground='white')


hairdresser_var.trace('w', disable_fully_booked_dates)
disable_fully_booked_dates()  # Initial call to disable dates for the default hairdresser

# Time selection
time_label = ttk.Label(root, text="Select Time:")
time_label.pack(pady=(20, 5))
time_var = tk.StringVar(root)
time_var.set("9:00 am")  # Default value
time_menu = ttk.OptionMenu(root, time_var, "9:00 am", "9:00 am", "11:00 am", "1:00 pm", "4:00 pm")
time_menu.pack(pady=(0, 20))

# Service selection
service_label = ttk.Label(root, text="Select Services:")
service_label.pack(pady=(20, 5))
service_entry = ttk.Entry(root)
service_entry.pack(pady=(0, 20))

# Book button
book_button = ttk.Button(root, text="Book Appointment", command=book_appointment)
book_button.pack(pady=20)

# Run Tkinter main loop
root.mainloop()
