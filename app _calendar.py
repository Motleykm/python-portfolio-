import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
import requests
from datetime import datetime
import tkinter.messagebox as messagebox


def update_calendar():
    hairdresser = hairdresser_combobox.get()
    response = requests.post('http://127.0.0.1:5000/unavailable_dates', json={'hairdresser': hairdresser})
    unavailable_dates = response.json()

    cal.calevent_remove('unavailable')
    for date in unavailable_dates:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        cal.calevent_create(date_obj, 'Unavailable', 'unavailable')


def show_available_times():
    selected_date = cal.get_date()
    hairdresser = hairdresser_combobox.get()
    response = requests.post('http://127.0.0.1:5000/available_times',
                             json={'date': selected_date, 'hairdresser': hairdresser})
    available_times = response.json()
    times_combobox['values'] = available_times


def on_date_selected(event):
    selected_date = cal.get_date()
    day_of_week = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%A')
    day_label.config(text=f"Day: {day_of_week}")
    show_available_times()


def book_appointment():
    selected_date = cal.get_date()
    selected_time = times_combobox.get()
    hairdresser = hairdresser_combobox.get()
    email = email_entry.get()

    if not selected_time or not hairdresser or not email:
        messagebox.showerror("Error", "Please fill all fields.")
        return

    response = requests.post('http://127.0.0.1:5000/book',
                             json={'date': selected_date, 'time': selected_time, 'hairdresser': hairdresser,
                                   'email': email})
    if response.status_code == 200:
        messagebox.showinfo("Success", "Appointment booked successfully!")
        show_available_times()
    else:
        messagebox.showerror("Error", response.json().get('error', 'Failed to book appointment.'))


def cancel_appointment():
    selected_date = cal.get_date()
    selected_time = times_combobox.get()
    hairdresser = hairdresser_combobox.get()

    response = requests.post('http://127.0.0.1:5000/cancel',
                             json={'date': selected_date, 'time': selected_time, 'hairdresser': hairdresser})
    if response.status_code == 200:
        messagebox.showinfo("Success", "Appointment cancelled successfully!")
        show_available_times()
    else:
        messagebox.showerror("Error", response.json().get('error', 'Failed to cancel appointment.'))


root = tk.Tk()
root.title("Appointment Booking")

ttk.Label(root, text="Select Hairdresser:").pack(pady=10)
hairdresser_combobox = ttk.Combobox(root, values=["Shanice", "Jamil", "Arrinana", "Cherish"], state="readonly")
hairdresser_combobox.pack(pady=10)
hairdresser_combobox.bind("<<ComboboxSelected>>", lambda e: update_calendar())

ttk.Label(root, text="Select a Date:").pack(pady=10)
cal = Calendar(root, selectmode='day', year=2024, month=6, day=7)
cal.pack(pady=10)
cal.bind("<<CalendarSelected>>", on_date_selected)

day_label = ttk.Label(root, text="Day: ")
day_label.pack(pady=10)

ttk.Button(root, text="Show Available Times", command=show_available_times).pack(pady=20)

ttk.Label(root, text="Available Times:").pack(pady=10)
times_combobox = ttk.Combobox(root)
times_combobox.pack(pady=10)

ttk.Label(root, text="Email:").pack(pady=10)
email_entry = ttk.Entry(root)
email_entry.pack(pady=10)

ttk.Button(root, text="Book Appointment", command=book_appointment).pack(pady=10)
ttk.Button(root, text="Cancel Appointment", command=cancel_appointment).pack(pady=10)

root.mainloop()
