import calendar
import os
import uuid
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_mail import Mail, Message
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
    appointment_status = Column(Enum('booked', 'canceled', 'rescheduled', name='appointment_status'), nullable=False,
                                default='booked')


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


# Utility Functions
def generate_confirmation_number():
    return str(uuid.uuid4())


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
        app.logger.error(f"Error adding appointment: {e}")
        session.rollback()
    finally:
        session.close()


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


# Availability data
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
            app.logger.error(f'Error during registration: {e}')
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
        try:
            user = session_db.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                session['username'] = user.username
                flash('Logged in successfully.')
                return redirect(url_for('customer_account'))
            else:
                flash('Invalid username or password.')
                return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f'Error during login: {e}')
            flash('An error occurred during login. Please try again.')
            return redirect(url_for('login'))
        finally:
            session_db.close()

    return render_template('login.html')


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
    try:
        user = session_db.query(User).filter_by(username=username).first()
        if not user:
            flash('User not found.')
            return redirect(url_for('login'))

        # Fetch appointments based on the user's email
        appointments = session_db.query(Appointment).filter_by(email=user.email).all()

        return render_template('customer_account.html', user=user, appointments=appointments)

    except Exception as e:
        app.logger.error(f'Error retrieving customer account details: {e}')
        flash('An error occurred while retrieving your account details. Please try again.')
        return redirect(url_for('login'))

    finally:
        session_db.close()


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
        email = request.form.get('email')  # For guest booking
        guest_booking = 'guest_booking' in request.form  # Check if this is a guest booking

        # Determine if user is logged in or not
        logged_in_user = session.get('username')

        # Validate form data
        if not services_input or not date_str or not time_str or not hairdresser or (not email and not logged_in_user):
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

        # Determine email address (for guests or logged-in users)
        if logged_in_user:
            session_db = SessionLocal()
            user = session_db.query(User).filter_by(username=logged_in_user).first()
            email = user.email if user else email

        # Add the appointment to the database
        add_appointment(date, datetime.combine(date, time), ", ".join(selected_services), day, hairdresser, total_price,
                        email, confirmation_number)

        # Determine where to redirect
        if logged_in_user:
            # Account user booking
            flash('Your appointment has been booked successfully!', 'success')
            return redirect(url_for('view_previous_appointment'))
        else:
            # Guest booking: Redirect to the appointment details page
            flash('Your appointment has been booked successfully as a guest!', 'success')
            return render_template(
                'appointment_details.html',
                day=day,
                date=date_str,
                time=time_str,
                total_price=total_price,
                hairdresser=hairdresser,
                selected_services=selected_services,
                confirmation_number=confirmation_number,
                email=email
            )

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


# Route to cancel an appointment
@app.route('/cancel_appointment', methods=['GET', 'POST'])
def cancel_appointment():
    if request.method == 'GET':
        confirmation_number = request.args.get('confirmation_number')
        email = request.args.get('email')

        # Render the cancellation confirmation page if the required parameters are present
        if confirmation_number and email:
            return render_template('confirm_cancel.html', confirmation_number=confirmation_number, email=email)
        else:
            flash('Missing confirmation number or email for cancellation.')
            return redirect(url_for('appointment_form'))

    elif request.method == 'POST':
        confirmation_number = request.form.get('confirmation_number')
        email = request.form.get('email')

        if not confirmation_number or not email:
            flash('Missing confirmation number or email.')
            return redirect(url_for('appointment_form'))

        session_db = SessionLocal()
        try:
            # Query the appointment by confirmation number and email
            appointment = session_db.query(Appointment).filter_by(
                confirmation_number=confirmation_number, email=email).first()

            # Check if the appointment exists
            if appointment:
                app.logger.info(f'Appointment found: {appointment}')
                appointment.appointment_status = 'canceled'
                session_db.commit()
                app.logger.info('Appointment successfully canceled.')
                flash('Your appointment has been canceled successfully.', 'success')
            else:
                app.logger.info(
                    f'No appointment found with confirmation number {confirmation_number} and email {email}.')
                flash('Appointment not found. Please check your confirmation number and email.', 'danger')
        except Exception as e:
            session_db.rollback()  # Rollback the transaction in case of an error
            app.logger.error(f'Error occurred while canceling the appointment: {e}')
            flash('An error occurred while canceling your appointment. Please try again.', 'danger')
        finally:
            session_db.close()  # Ensure the session is closed

        return redirect(url_for('appointment_form'))


# Route to reschedule an appointment
@app.route('/reschedule_appointment', methods=['POST'])
def reschedule_appointment():
    confirmation_number = request.form.get('confirmation_number')
    email = request.form.get('email')
    new_date_str = request.form.get('new_date')
    new_time_str = request.form.get('new_time')

    if not confirmation_number or not email or not new_date_str or not new_time_str:
        flash('Please fill out all fields.')
        return redirect(url_for('appointment_form'))

    session_db = SessionLocal()
    try:
        # Query the appointment by confirmation number and email
        appointment = session_db.query(Appointment).filter_by(
            confirmation_number=confirmation_number, email=email).first()

        if not appointment:
            flash('Appointment not found.')
            return redirect(url_for('appointment_form'))

        # Parse the new date and time
        new_date = datetime.strptime(new_date_str, '%Y-%m-%d')
        new_time = datetime.strptime(new_time_str, '%I:%M %p').time()
        day = new_date.strftime('%A')

        # Check if the selected time is available
        fully_booked, available_times = is_fully_booked(appointment.hairdresser, new_date)
        if fully_booked or new_time_str not in available_times:
            flash(f'The selected time is not available. Please choose another time.', 'danger')
            return redirect(url_for('appointment_form'))

        # Update the appointment details
        appointment.date = new_date
        appointment.time = datetime.combine(new_date, new_time)
        appointment.day = day
        session_db.commit()

        flash('Your appointment has been rescheduled successfully.', 'success')
        return redirect(url_for('view_previous_appointment'))

    except Exception as e:
        session_db.rollback()
        app.logger.error(f'Error rescheduling appointment: {e}')
        flash('An error occurred while rescheduling your appointment. Please try again.', 'danger')
        return redirect(url_for('appointment_form'))
    finally:
        session_db.close()


# Route to view the last appointment
@app.route('/view_previous_appointments', methods=['GET'])
def view_previous_appointment():
    if 'username' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    username = session['username']

    session_db = SessionLocal()
    try:
        # Fetch the user based on the username
        user = session_db.query(User).filter_by(username=username).first()
        if not user:
            flash('User not found.')
            return redirect(url_for('login'))

        # Fetch the last appointment for the user based on their email
        appointments = session_db.query(Appointment).filter_by(email=user.email).order_by(
            Appointment.date.desc(), Appointment.time.desc()).all()

        if not appointments:
            flash('No appointments found.')
            return redirect(url_for('customer_account'))

        # Render a template to display the appointments
        return render_template('customer_account_details.html', appointments=appointments, user=user)
    except Exception as e:
        app.logger.error(f"Error fetching last appointment: {e}")
        flash('An error occurred while fetching your appointment. Please try again later.')
        return redirect(url_for('customer_account'))
    finally:
        session_db.close()


# Route to confirm an appointment and send an email
@app.route('/confirm_appointment', methods=['POST'])
def confirm_appointment():
    confirmation_number = request.form.get('confirmation_number')
    email = request.form.get('email')

    session_db = SessionLocal()
    try:
        # Query the appointment by confirmation number
        appointment = session_db.query(Appointment).filter_by(confirmation_number=confirmation_number,
                                                              email=email).first()

        if not appointment:
            flash('Appointment not found.')
            return redirect(url_for('appointment_form'))

        # Send confirmation email
        subject = "Appointment Confirmation"
        body = f"Dear Customer,\n\nYour appointment with {appointment.hairdresser} on {appointment.date.strftime('%A, %B %d, %Y')} at {appointment.time.strftime('%I:%M %p')} has been confirmed.\n\nServices: {appointment.service}\nTotal Cost: ${appointment.cost}\n\nThank you for choosing us!\n\nConfirmation Number: {appointment.confirmation_number}"

        try:
            msg = Message(subject, sender='kmotley09@gmail.com', recipients=[email])
            msg.body = body
            mail.send(msg)
            flash('Confirmation email sent successfully!', 'success')
        except Exception as e:
            app.logger.error(f"Error sending email: {e}")
            flash('Failed to send confirmation email. Please try again.', 'danger')

        # Redirect to a success page or the user's account page
        if 'username' in session:
            return redirect(url_for('view_previous_appointment'))
        else:
            return redirect(url_for('appointment_form'))

    except Exception as e:
        session_db.rollback()
        app.logger.error(f'Error confirming appointment: {e}')
        flash('An error occurred while confirming your appointment. Please try again.', 'danger')
        return redirect(url_for('appointment_form'))
    finally:
        session_db.close()


# Route to delete a user account
@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if 'username' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))

    username = session['username']
    session_db = SessionLocal()

    try:
        user = session_db.query(User).filter_by(username=username).first()

        if user:
            session_db.delete(user)
            session_db.commit()
            session.pop('username', None)  # Log out the user after account deletion
            flash('Account successfully deleted.')
            return redirect(url_for('signup'))
        else:
            flash('No account found.')
            return redirect(url_for('customer_account'))
    except Exception as e:
        session_db.rollback()
        app.logger.error(f'Error occurred while deleting account: {e}')
        flash('An error occurred while deleting your account. Please try again.')
        return redirect(url_for('customer_account'))
    finally:
        session_db.close()


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


# Route to cancel an appointment from the user account
# Route to cancel an appointment via email link
@app.route('/cancel_appointment_email/<confirmation_id>', methods=['GET'])
def cancel_appointment_email(confirmation_id):
    session_db = SessionLocal()
    try:
        # Query the appointment by confirmation number
        appointment = session_db.query(Appointment).filter_by(confirmation_number=confirmation_id).first()

        if not appointment:
            flash('Appointment not found.')
            return redirect(url_for('appointment_form'))

        # Mark the appointment as canceled
        appointment.appointment_status = 'canceled'
        session_db.commit()

        flash('Your appointment has been canceled successfully.', 'success')

        # Fetch updated appointments
        username = session.get('username')
        if username:
            user = session_db.query(User).filter_by(username=username).first()
            appointments = session_db.query(Appointment).filter_by(email=user.email).all()
            return render_template('customer_account.html', user=user, appointments=appointments)
        else:
            return redirect(url_for('appointment_form'))

    except Exception as e:
        session_db.rollback()
        app.logger.error(f'Error occurred while canceling the appointment: {e}')
        flash('An error occurred while canceling your appointment. Please try again.', 'danger')
        return redirect(url_for('appointment_form'))
    finally:
        session_db.close()


@app.route('/send_confirmation_email', methods=['POST'])
@app.route('/send_confirmation_email/<int:appointment_id>', methods=['GET'])
def send_confirmation_email(appointment_id):
    session_db = SessionLocal()
    try:
        # Retrieve the appointment details
        appointment = session_db.query(Appointment).filter_by(id=appointment_id).first()
        if not appointment:
            flash('Appointment not found.', 'error')
            return redirect(url_for('customer_account'))

        # Prepare the confirmation email
        subject = "Your Appointment Confirmation"
        body = f"Dear {appointment.email},\n\n" \
               f"Your appointment for {appointment.service} on {appointment.date.strftime('%Y-%m-%d')} at {appointment.time.strftime('%H:%M %p')} " \
               f"has been confirmed.\n\nYour confirmation number is {appointment.confirmation_number}."

        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[appointment.email])
        msg.body = body
        mail.send(msg)

        flash('Confirmation email sent successfully!', 'success')
    except Exception as e:
        app.logger.error(f'Failed to send confirmation email: {e}')
        flash('Failed to send confirmation email.', 'error')
    finally:
        session_db.close()
    return redirect(url_for('customer_account'))


@app.route('/show_reschedule_form/<int:appointment_id>', methods=['GET'])
def show_reschedule_form(appointment_id):
    # Authentication and authorization checks
    if 'user_id' not in session:
        flash("Please log in to access this page.", "warning")
        return redirect(url_for('login'))

    # Retrieving the appointment details
    appointment = Appointment.query.get(appointment_id)
    if not appointment or appointment.user_id != session['user_id']:
        flash("You do not have permission to reschedule this appointment.", "error")
        return redirect(url_for('dashboard'))

    # Show the rescheduling form
    return render_template('reschedule_form.html', appointment=appointment)





if __name__ == '__main__':
    app.run(debug=True)
