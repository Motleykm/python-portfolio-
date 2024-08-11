import calendar
import os
import uuid
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mail import Mail
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
# Import the price calculator module
from utilities.price_calculator import (
    REG_HAIRSTYLES_PRICES,
    WEAVE_HAIRSTYLES_PRICES,
    BRAIDS_AND_LOCS_PRICES,
    HAIRCUT_STYLES_PRICES,
    calculate_total_price
)
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Set the secret key for session management
app.secret_key = os.urandom(24)

# Database configuration
DATABASE_URL = "sqlite:///newupdatedappointment.db"
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'kmotley09@gmail.com'
app.config['MAIL_PASSWORD'] = 'cprf swoh rnfo snhl'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


# Define the Appointment model
class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    time = Column(DateTime, nullable=False)
    service = Column(String, nullable=False)
    day = Column(String, nullable=False)
    hairdresser = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    email = Column(String, nullable=False)
    confirmation_number = Column(String, nullable=False, unique=True)
    appointment_status = Column(Enum('booked', 'canceled', name='appointment_status'), nullable=False, default='booked')


# Define the User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password = Column(String(150), nullable=False)


# Create the database tables
Base.metadata.create_all(engine)


# Function to generate a unique confirmation number
def generate_confirmation_number():
    return str(uuid.uuid4())


# Function to add an appointment to the database
def add_appointment(date, time, service, day, hairdresser, cost, email, confirmation_number):
    session = SessionLocal()
    try:
        new_appointment = Appointment(
            date=date, time=time, service=service, day=day, hairdresser=hairdresser,
            cost=cost, email=email, confirmation_number=confirmation_number
        )
        session.add(new_appointment)
        session.commit()
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()


# Define day availability and times dictionary
availability_day = {
    "Monday": {
        "Shanice": ["9:00 am", "11:00 am", "1:00 pm", "4:00 pm"],
        "Jamil": ["10:00 am", "12:00 pm", "2:00 pm", "4:00 pm"]
    },
    "Tuesday": {
        "Arrinana": ["10:00 am", "2:00 pm", "3:00 pm", "6:00 pm"],
        "Cherish": ["11:00 am", "4:00 pm", "5:00 pm", "6:00 pm"]
    },
    "Wednesday": {
        "Arrinana": ["9:00 am", "12:00 pm", "3:00 pm", "5:00 pm"],
        "Jamil": ["10:00 am", "5:00 pm"],
        "Cherish": ["11:00 am", "4:30 pm"]
    },
    "Thursday": {
        "Shanice": ["9:00 am", "3:00 pm", "4:00 pm", "5:00 pm"],
        "Jamil": ["9:00 am", "3:00 pm", "4:00 pm", "5:00 pm"],
        "Cherish": ["10:00 am", "5:00 pm"]
    },
    "Friday": {
        "Shanice": ["10:00 am", "12:00 pm", "2:00 pm", "5:00 pm"],
        "Jamil": ["10:00 am", "3:00 pm", "4:00 pm", "6:00 pm"],
        "Cherish": ["10:00 am", "5:00 pm"]
    },
    "Saturday": {
        "Shanice": ["10:00 am", "12:00 pm", "2:00 pm", "4:00 pm"],
        "Jamil": ["9:00 am", "4:00 pm"],
        "Cherish": ["10:00 am", "4:00 pm"]
    },
    "Sunday": {
        "Jamil": [],
        "Cherish": [],
        "Shanice": [],
        "Arrinana": []
    }
}


# Validation functions
def validate_full_name(full_name):
    if full_name and isinstance(full_name, str):
        return "Valid full name"
    return "Invalid full name"


def validate_username(username):
    if username and isinstance(username, str) and len(username) >= 3:
        return "Valid username"
    return "Invalid username"


def validate_email(email):
    if email and "@" in email:
        return "Valid email"
    return "Invalid email"


def validate_password(password):
    if password and len(password) >= 6:
        return "Valid password"
    return "Invalid password"


# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate inputs
        full_name_validation = validate_full_name(full_name)
        username_validation = validate_username(username)
        email_validation = validate_email(email)
        password_validation = validate_password(password)

        if full_name_validation != "Valid full name":
            flash(full_name_validation)
            return redirect(url_for('register'))
        if username_validation != "Valid username":
            flash(username_validation)
            return redirect(url_for('register'))
        if email_validation != "Valid email":
            flash(email_validation)
            return redirect(url_for('register'))
        if password_validation != "Valid password":
            flash(password_validation)
            return redirect(url_for('register'))
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for('signup'))

        session = SessionLocal()
        try:
            # Check if the email or username already exists
            if session.query(User).filter_by(email=email).first() or session.query(User).filter_by(
                    username=username).first():
                flash('Email or username already exists.')
                return redirect(url_for('register'))

            # Hash the password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            # Create a new user
            new_user = User(full_name=full_name, username=username, email=email, password=hashed_password)

            # Save the user to the database
            session.add(new_user)
            session.commit()

            flash('User registered successfully.')
            return redirect(url_for('appointment_form'))
        except Exception as e:
            session.rollback()
            flash(f'Error: {e}')
            return redirect(url_for('register'))
        finally:
            session.close()
    return render_template('signup.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        session_db = SessionLocal()
        user = session_db.query(User).filter_by(username=username).first()
        session_db.close()

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            flash('Logged in successfully.')
            return redirect(url_for('customer_account'))
        else:
            flash('Invalid username or password.')
            return redirect(url_for('login'))

    return render_template('customer_login.html')


# Logout route
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    flash('Logged out successfully.')
    return redirect(url_for('logout_success'))


@app.route('/logout_success')
def logout_success():
    return render_template('index.html')


# Customer account route
@app.route('/customer_account', methods=['GET', 'POST'])
def customer_account():
    if 'username' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    username = session['username']

    session_db = SessionLocal()
    user = session_db.query(User).filter_by(username=username).first()
    if not user:
        flash('User not found.')
        return redirect(url_for('login'))

    # Fetch appointments based on the user's email
    appointments = session_db.query(Appointment).filter_by(email=user.email).all()
    session_db.close()

    return render_template('customer_account_details.html', user=user, appointments=appointments)


# Appointment form route
@app.route('/')
def appointment_form():
    services = (
            list(REG_HAIRSTYLES_PRICES.keys()) + list(WEAVE_HAIRSTYLES_PRICES.keys()) +
            list(BRAIDS_AND_LOCS_PRICES.keys()) + list(HAIRCUT_STYLES_PRICES.keys())
    )
    return render_template('index.html', services=services, availability=availability_day)


# Function to get the day from a date
@app.route('/get_day_from_date', methods=['POST'])
def get_day_from_date():
    data = request.json
    date_str = data.get('date')

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = calendar.day_name[date_obj.weekday()]
        return jsonify({'day': day_name})
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400


# Function to get hairdresser availability
@app.route('/hairdresser_availability', methods=['POST'])
def hairdresser_availability():
    data = request.json
    date_str = data.get('date')
    hairdresser = data.get('hairdresser')

    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = calendar.day_name[date_obj.weekday()]
        available_times = availability_day.get(day_name, {}).get(hairdresser, [])
        return jsonify({'availability': available_times})
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400


# Function to get hairdresser's full availability
@app.route('/hairdresser_full_availability', methods=['POST'])
def hairdresser_full_availability():
    data = request.json
    hairdresser = data.get('hairdresser')

    try:
        start_date = datetime.today()
        end_date = start_date + timedelta(days=365)

        unavailable_dates = []
        current_date = start_date
        while current_date <= end_date:
            day_name = calendar.day_name[current_date.weekday()]
            if hairdresser not in availability_day.get(day_name, {}):
                unavailable_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

        return jsonify({'unavailable_dates': unavailable_dates})
    except ValueError:
        return jsonify({'error': 'Invalid request format'}), 400


# Function to book an appointment
@app.route('/submit_appointment', methods=['POST'])
def book_appointment():
    try:
        # Get form data
        services_input = request.form.get('services')
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        hairdresser = request.form.get('hairdresser')
        email = request.form.get('email')
        guest_booking = request.form.get('guest_booking')  # Flag to check if booking as a guest

        # Validate form data
        if not services_input or not date_str or not time_str or not hairdresser or not email:
            raise ValueError('Please fill out all fields.')

        selected_services = [service.strip() for service in services_input.split(',')]
        date = datetime.strptime(date_str, '%Y-%m-%d')
        time = datetime.strptime(time_str, '%I:%M %p').time()
        day = date.strftime('%A')

        # Check if the selected day is Sunday
        if day == "Sunday":
            raise ValueError('Sorry, we are closed on Sundays. Please select another day.')

        # Check if the hairdresser is fully booked
        fully_booked, available_times = is_fully_booked(hairdresser, date)
        if fully_booked:
            raise ValueError('Sorry, the hairdresser is fully booked.')

        # Check if the selected time is available
        if time_str not in available_times:
            raise ValueError(f'Selected time is not available. Available times: {", ".join(available_times)}')

        # Validate services
        for service in selected_services:
            if (service not in REG_HAIRSTYLES_PRICES and
                service not in WEAVE_HAIRSTYLES_PRICES and
                service not in BRAIDS_AND_LOCS_PRICES and
                    service not in HAIRCUT_STYLES_PRICES):
                raise ValueError('One or more selected services are not provided.')

        # Calculate the total price
        total_price = calculate_total_price(selected_services)
        confirmation_number = generate_confirmation_number()

        # Add the appointment to the database
        add_appointment(date, datetime.combine(date, time), ", ".join(selected_services), day, hairdresser, total_price,
                        email, confirmation_number)

        if guest_booking:
            # Guest booking: just show the appointment details without logging in
            flash('Your appointment has been booked successfully as a guest!', 'success')
            return render_template(
                'appointment_details.html', day=day, date=date_str, time=time_str, total_price=total_price,
                hairdresser=hairdresser, selected_services=selected_services, confirmation_number=confirmation_number,
                email=email
            )
        else:
            # Registered user: show the customer's account detailsc
            session_db = SessionLocal()
            user = session_db.query(User).filter_by(email=email).first()
            appointments = session_db.query(Appointment).filter_by(email=email).all()
            session_db.close()

            flash('Your appointment has been booked successfully!', 'success')
            return render_template('customer_details.html', user=user, appointments=appointments)

    except ValueError as ve:
        app.logger.error(f'Validation error: {ve}')
        flash(str(ve), 'danger')
        return redirect(url_for('appointment_form'))
    except KeyError as e:
        app.logger.error(f'Missing key in form data: {e}')
        flash('An error occurred while processing your request. Please try again.', 'danger')
        return redirect(url_for('appointment_form'))
    except Exception as e:
        app.logger.error(f'Error processing appointment submission: {e}')
        flash('An unexpected error occurred. Please try again later.', 'danger')
        return redirect(url_for('appointment_form'))


# Function to check if a hairdresser is fully booked on a specific date
def is_fully_booked(hairdresser, date):
    session = SessionLocal()
    try:
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        appointments = session.query(Appointment).filter(
            Appointment.hairdresser == hairdresser,
            Appointment.date == date,
            Appointment.time >= date_start,
            Appointment.time <= date_end,
            Appointment.appointment_status == 'booked'
        ).all()

        day_name = calendar.day_name[date.weekday()]
        available_times = availability_day.get(day_name, {}).get(hairdresser, [])

        booked_times = {appt.time.strftime('%I:%M %p') for appt in appointments}
        available_times = [time for time in available_times if time not in booked_times]

        return not available_times, available_times
    finally:
        session.close()


# Route to view the last appointment
@app.route('/view_last_appointment', methods=['GET', 'POST'])
def view_last_appointment():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Email is required to view your last appointment.')
            return redirect(url_for('appointment_form'))

        session = SessionLocal()
        try:
            last_appointment = session.query(Appointment).filter_by(email=email).order_by(
                Appointment.time.desc()).first()
            if not last_appointment:
                flash('No appointment found for the provided email.')
                return redirect(url_for('appointment_form'))

            return render_template('view_last_appointment.html', appointment=last_appointment)
        except Exception as e:
            app.logger.error(f'Error fetching last appointment: {str(e)}')
            flash('An error occurred while fetching your appointment.')
            return redirect(url_for('appointment_form'))
        finally:
            session.close()
    else:
        return render_template('view_last_appointment.html', appointment=None)


# Route to get fully booked dates for hairdressers
@app.route('/get_fully_booked_dates', methods=['GET'])
def get_fully_booked_dates():
    session = SessionLocal()
    try:
        appointments = session.query(Appointment).filter_by(appointment_status='booked').all()
        fully_booked_dates = {}
        for appointment in appointments:
            if appointment.hairdresser not in fully_booked_dates:
                fully_booked_dates[appointment.hairdresser] = []
            fully_booked_dates[appointment.hairdresser].append(appointment.date.strftime('%Y-%m-%d'))
        return jsonify(fully_booked_dates)
    except Exception as e:
        app.logger.error(f'Error fetching fully booked dates: {str(e)}')
        return jsonify({"error": "Failed to fetch fully booked dates"}), 500
    finally:
        session.close()


# Function to generate unavailable dates for a hairdresser
def generate_unavailable_dates(hairdresser):
    unavailable_dates = []
    start_date = datetime.today()
    end_date = start_date + timedelta(days=365)  # Adjust the range as needed

    current_date = start_date
    while current_date <= end_date:
        day_name = current_date.strftime('%A')
        if hairdresser not in availability_day.get(day_name, {}):
            unavailable_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    return unavailable_dates


# Route to get unavailable dates for a hairdresser
@app.route('/unavailable_dates', methods=['POST'])
def unavailable_dates():
    hairdresser = request.json['hairdresser']
    unavailable_dates = generate_unavailable_dates(hairdresser)
    return jsonify(unavailable_dates)


# Route to get available times for a hairdresser on a specific date
@app.route('/available_times', methods=['POST'])
def available_times():
    selected_date = request.json['date']
    hairdresser = request.json['hairdresser']
    day_name = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%A')
    times = availability_day.get(day_name, {}).get(hairdresser, [])
    return jsonify(times)


# Route to get available times for a specific date
@app.route('/get_available_times', methods=['POST'])
def get_available_times():
    data = request.get_json()
    hairdresser = data.get('hairdresser')
    date = data.get('date')
    # Fetch available times from predefined data
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    day_name = calendar.day_name[date_obj.weekday()]
    available_times = availability_day.get(day_name, {}).get(hairdresser, [])
    return jsonify({'available_times': available_times})


if __name__ == '__main__':
    app.run(debug=True)
