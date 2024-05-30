from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message

from utilities.price_calculator import (
    REG_HAIRSTYLES_PRICES,
    WEAVE_HAIRSTYLES_PRICES,
    BRAIDS_AND_LOCS_PRICES,
    HAIRCUT_STYLES_PRICES,
    calculate_total_price
)
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

DATABASE_URL = "sqlite:///appointments.db"

app = Flask(__name__)


# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = ( 'kmotley09@gmail.com')
app.config['MAIL_PASSWORD'] = ( 'ktzq qreu rqoa wprv')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# Define the Appointment model
class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, nullable=False)
    service = Column(String, nullable=False)
    day = Column(String, nullable=False)
    hairdresser = Column(String, nullable=False)
    cost = Column(Float, nullable=False)
    email = Column(String, nullable=False)
    confirmation_number = Column(String, nullable=True, unique=True)

# Create the database tables
Base.metadata.create_all(engine)

# Create a configured "Session" class
SessionLocal = sessionmaker(bind=engine)

def generate_confirmation_number():
    return str(uuid.uuid4())

def add_appointment(time, service, day, hairdresser, cost, email, confirmation_number):
    session = SessionLocal()
    try:
        new_appointment = Appointment(
            time=time, service=service, day=day, hairdresser=hairdresser,
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

@app.route('/')
def appointment_form():
    services = (
        list(REG_HAIRSTYLES_PRICES.keys()) + list(WEAVE_HAIRSTYLES_PRICES.keys()) +
        list(BRAIDS_AND_LOCS_PRICES.keys()) + list(HAIRCUT_STYLES_PRICES.keys())
    )
    return render_template('index.html', services=services, availability=availability_day)

@app.route('/submit_appointment', methods=['POST'])
def book_appointment():
    try:
        services_input = request.form.get('services')
        if not services_input:
            return render_template('error.html', error_message='Please select at least one service.')

        selected_services = [service.strip() for service in services_input.split(',')]
        day = request.form.get('day')
        time = request.form.get('time')
        hairdresser = request.form.get('hairdresser')

        if not all([day, time, hairdresser]):
            return render_template('error.html', error_message='Please fill out all fields.')

        if day == "Sunday":
            return render_template('closed.html', error_message='Sorry, we are closed on Sundays. Please select another day')

        for service in selected_services:
            if (
                service not in REG_HAIRSTYLES_PRICES and
                service not in WEAVE_HAIRSTYLES_PRICES and
                service not in BRAIDS_AND_LOCS_PRICES and
                service not in HAIRCUT_STYLES_PRICES
            ):
                return render_template('error.html', error_message='One or more selected services are not provided.')

        if hairdresser not in availability_day.get(day, {}):
            return render_template('error.html', error_message='Selected hairdresser is not available on this day.')

        if time not in availability_day[day].get(hairdresser, []):
            available_times = ", ".join(availability_day[day].get(hairdresser, []))
            return render_template('error.html', error_message=f'Selected time is not available. Available times: {available_times}')

        total_price = calculate_total_price(selected_services)
        confirmation_number = generate_confirmation_number()

        return render_template(
            'appointment_details.html', day=day, time=time, total_price=total_price,
            hairdresser=hairdresser, selected_services=selected_services, confirmation_number=confirmation_number
        )
    except Exception as e:
        app.logger.error(f'Error processing appointment submission: {e}')
        return render_template('error.html', error_message='An error occurred while processing your request.')

@app.route('/confirm_appointment', methods=['POST'])
def confirm_appointment():
    try:
        day = request.form.get('day')
        time_str = request.form.get('time')
        hairdresser = request.form.get('hairdresser')
        selected_services = request.form.get('services').split(', ')
        email = request.form.get('email')
        confirmation_number = request.form.get('confirmation_number')

        datetime_format = "%I:%M %p"
        appointment_datetime = datetime.strptime(time_str, datetime_format).replace(year=datetime.now().year, month=datetime.now().month, day=datetime.now().day)

        add_appointment(
            time=appointment_datetime,
            service=", ".join(selected_services),
            day=day,
            hairdresser=hairdresser,
            cost=calculate_total_price(selected_services),
            email=email,
            confirmation_number=confirmation_number
        )

        msg = Message(
            'Appointment Confirmation',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.html = f"""
            <h3>Appointment Confirmation</h3>
            <p><strong>Day:</strong> {day}</p>
            <p><strong>Time:</strong> {time_str}</p>
            <p><strong>Hairdresser:</strong> {hairdresser}</p>
            <p><strong>Services:</strong> {', '.join(selected_services)}</p>
            <p><strong>Total Price:</strong> ${calculate_total_price(selected_services)}</p>
            <p><strong>Confirmation Number:</strong> {confirmation_number}</p>
            <p><a href="{url_for('cancel_appointment_email', confirmation_number=confirmation_number, _external=True)}">Cancel Appointment</a></p>
        """

        mail.send(msg)
        return 'Appointment confirmation email sent successfully!'
    except Exception as e:
        app.logger.error(f'Error sending confirmation email: {str(e)}')
        return 'An error occurred while processing'

@app.route('/cancel_appointment_email/<confirmation_number>', methods=['GET'])
def cancel_appointment_email(confirmation_number):
    session = SessionLocal()
    try:
        appointment = session.query(Appointment).filter_by(confirmation_number=confirmation_number).first()
        if not appointment:
            return render_template('cancel_appointment.html', message='Appointment not found.', error=True)

        email = appointment.email
        session.delete(appointment)
        session.commit()

        send_cancellation_email(email)
        return render_template('cancel_appointment.html', message='Your appointment has been successfully canceled.')
    except Exception as e:
        session.rollback()
        app.logger.error(f'Error cancelling appointment: {str(e)}')
        return render_template('cancel_appointment.html', message='An error occurred while cancelling the appointment.', error=True)
    finally:
        session.close()

def send_cancellation_email(email):
    try:
        msg = Message(
            'Appointment Cancellation',
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = 'Your appointment has been successfully canceled.'
        mail.send(msg)
    except Exception as e:
        app.logger.error(f'Error sending cancellation email: {str(e)}')

@app.route('/cancel_appointment', methods=['POST'])
def cancel_appointment():
    try:
        appointment_id = request.form.get('appointment_id')
        if not appointment_id:
            flash('Appointment ID is required.')
            return redirect(url_for('appointment_form'))

        session = SessionLocal()
        try:
            appointment = session.query(Appointment).filter_by(id=appointment_id).first()
            if not appointment:
                flash('Appointment not found.')
                return redirect(url_for('appointment_form'))

            email = appointment.email
            session.delete(appointment)
            session.commit()

            send_cancellation_email(email)
            flash('Appointment cancelled successfully.')
            return render_template('cancel_appointment.html', message='Your appointment has been successfully canceled.')
        except Exception as e:
            session.rollback()
            app.logger.error(f'Error cancelling appointment: {str(e)}')
            flash('An error occurred while cancelling the appointment.')
            return redirect(url_for('appointment_form'))
        finally:
            session.close()
    except Exception as e:
        app.logger.error(f'Error processing cancellation: {str(e)}')
        flash('An error occurred while processing your request.')
        return redirect(url_for('appointment_form'))

if __name__ == "__main__":
    app.run(debug=True)
