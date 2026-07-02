import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()  # reads variables from a local .env file

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not SENDER_EMAIL or not APP_PASSWORD:
    raise RuntimeError(
        "SENDER_EMAIL and APP_PASSWORD must be set in your .env file."
    )

def send_reminder(receiver_email, company_name, role, package, visit_date):

    # Create email
    message = MIMEMultipart()

    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email
    message["Subject"] = f"Placement Reminder - {company_name}"

    body = f"""
Hello,

This is a reminder that {company_name} is visiting your campus soon.

Company : {company_name}
Role    : {role}
Package : {package} LPA
Visit   : {visit_date}

Make sure you revise:
✔ DSA
✔ SQL
✔ Aptitude
✔ HR Questions

Good luck!

Campus Placement Tracker
"""

    message.attach(MIMEText(body, "plain"))

    # Connect to Gmail SMTP
    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(SENDER_EMAIL, APP_PASSWORD)

    server.sendmail(
        SENDER_EMAIL,
        receiver_email,
        message.as_string()
    )

    server.quit()

    print("Email sent successfully!")