import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Replace with your own Gmail address
SENDER_EMAIL = "nagarwal_be24@thapar.edu"

# Replace with your 16-character App Password
APP_PASSWORD = "crdt wmfw bmfd mzxs"

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