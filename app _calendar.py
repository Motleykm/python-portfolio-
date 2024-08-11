import json
import tkinter as tk
from tkinter import ttk

import requests
from tkcalendar import Calendar


def submit_appointment():
    date = calendar.get_date()
    time = time_var.get()
    service = service_var.get()
    hairdresser = hairdresser_var.get()

    # Prepare data to be sent to the Flask backend
    data = {
        'date': date,
        'time': time,
        'service': service,
        'hairdresser': hairdresser
    }

    # First, check availability
    availability_response = requests.post(
        'http://localhost:5000/hairdresser_full_availability',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'hairdresser': hairdresser, 'date': date})
    )

    if availability_response.status_code == 200:
        # If available, proceed to book the appointment
        appointment_response = requests.post(
            'http://localhost:5000/submit_appointment',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(data)
        )

        if appointment_response.status_code == 200:
            result_label.config(text='Appointment booked successfully!')
        else:
            result_label.config(text=f'Failed to book appointment: {appointment_response.text}')
    else:
        result_label.config(text=f'Failed to fetch availability: {availability_response.text}')


# Create the main window
root = tk.Tk()
root.title('Appointment Booking')

# Create and place UI elements
ttk.Label(root, text='Select Date:').grid(row=0, column=0, padx=10, pady=10)
calendar = Calendar(root)
calendar.grid(row=0, column=1, padx=10, pady=10)

ttk.Label(root, text='Select Time:').grid(row=1, column=0, padx=10, pady=10)
time_var = tk.StringVar()
time_options = ['9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM']
time_menu = ttk.OptionMenu(root, time_var, time_options[0], *time_options)
time_menu.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(root, text='Select Service:').grid(row=2, column=0, padx=10, pady=10)
service_var = tk.StringVar()
service_options = ['Haircut', 'Color', 'Styling']
service_menu = ttk.OptionMenu(root, service_var, service_options[0], *service_options)
service_menu.grid(row=2, column=1, padx=10, pady=10)

ttk.Label(root, text='Select Hairdresser:').grid(row=3, column=0, padx=10, pady=10)
hairdresser_var = tk.StringVar()
hairdresser_options = ['Shanice', 'Jamil', 'Cherish']
hairdresser_menu = ttk.OptionMenu(root, hairdresser_var, hairdresser_options[0], *hairdresser_options)
hairdresser_menu.grid(row=3, column=1, padx=10, pady=10)

submit_button = ttk.Button(root, text='Book Appointment', command=submit_appointment)
submit_button.grid(row=4, column=0, columnspan=2, pady=10)

result_label = ttk.Label(root, text='')
result_label.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
