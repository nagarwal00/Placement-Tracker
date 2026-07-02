import os
from werkzeug.security import generate_password_hash, check_password_hash
import re

from flask import Flask, render_template, request, redirect
import sqlite3
from email_utils import send_reminder
from dotenv import load_dotenv
python-dotenv==1.0.1


from flask import Flask, render_template, request, redirect, session

load_dotenv()

app = Flask(__name__)

def valid_password(password):

    if len(password) < 8:
        return False

    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

    return re.match(pattern, password)

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY must be set in your .env file.")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
def add_company():

    if "user_id" not in session:
       return redirect("/login")

    if request.method == "POST":

        name = request.form["name"]
        role = request.form["role"]
        package = request.form["package"]
        visit_date = request.form["visit_date"]
        eligibility = request.form["eligibility"]

        user_id = session["user_id"]

        conn = sqlite3.connect("placement.db")
        cursor = conn.cursor()

        # Insert company
        cursor.execute("""
        INSERT INTO companies(name, role, package, visit_date, eligibility, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, role, package, visit_date, eligibility, user_id))

        # Get the ID of the inserted company
        company_id = cursor.lastrowid

        # Create prep_status for this company
        cursor.execute("""
        INSERT INTO prep_status(company_id, dsa_done, resume_done, hr_done, notes)
        VALUES (?, 0, 0, 0, '')
        """, (company_id,))

        conn.commit()
        conn.close()

        return redirect("/companies")

    return render_template("add_company.html")

@app.route("/companies")
def companies():

    if "user_id" not in session:
      return redirect("/login")

    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()

    user_id = session["user_id"]


    # Get search text from URL
    search = request.args.get("search")

    if search:
        cursor.execute("""
        SELECT * FROM companies
        WHERE user_id = ? AND name LIKE ?
        """, (user_id, '%' + search + '%'))
    else:
        cursor.execute("""
        SELECT * FROM companies
        WHERE user_id = ?
        """, (user_id,))

    companies = cursor.fetchall()

    conn.close()

    return render_template(
        "companies.html",
        companies=companies,
        search=search
    )
@app.route("/prep/<int:company_id>", methods=["GET", "POST"])
def prep(company_id):

    if "user_id" not in session:
      return redirect("/login")

    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()

    # If Save button is clicked
    if request.method == "POST":

        dsa = 1 if "dsa" in request.form else 0
        resume = 1 if "resume" in request.form else 0
        hr = 1 if "hr" in request.form else 0

        cursor.execute("""
            UPDATE prep_status
            SET dsa_done=?,
                resume_done=?,
                hr_done=?
            WHERE company_id=?
        """, (dsa, resume, hr, company_id))

        conn.commit()

    # Read company details
    user_id = session["user_id"]

    cursor.execute("""
    SELECT *
    FROM companies
    WHERE id=? AND user_id=?
    """, (company_id, user_id))
    company = cursor.fetchone()
    if company is None:
      conn.close()
      return "Access Denied!"
    

    # Read preparation status
    cursor.execute(
        "SELECT * FROM prep_status WHERE company_id=?",
        (company_id,)
    )
    prep = cursor.fetchone()
    completed = prep[2] + prep[3] + prep[4]

    progress = int((completed / 3) * 100)
    

    conn.close()

    return render_template(
    "prep.html",
    company=company,
    prep=prep,
    progress=progress
)
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
       return redirect("/login")

    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()
    user_id = session["user_id"]

    # Total companies
    cursor.execute("""
    SELECT COUNT(*)
    FROM companies
    WHERE user_id = ?
    """, (user_id,))
    total_companies = cursor.fetchone()[0]

    # Highest package
    cursor.execute("""
    SELECT MAX(package)
    FROM companies
    WHERE user_id = ?
    """, (user_id,))   
    highest_package = cursor.fetchone()[0]
    if highest_package is None:
       highest_package = 0
 
    # Average package
    cursor.execute("""
    SELECT AVG(package)
    FROM companies
    WHERE user_id = ?
    """, (user_id,))
    average_package = cursor.fetchone()[0]
    if average_package is None:
       average_package = 0

    
    # Overall Preparation Percentage

    cursor.execute("""
    SELECT
    SUM(prep_status.dsa_done),
    SUM(prep_status.resume_done),
    SUM(prep_status.hr_done)
    FROM prep_status
    JOIN companies
    ON prep_status.company_id = companies.id
    WHERE companies.user_id = ?
    """, (user_id,))

    prep = cursor.fetchone()

    completed_tasks = sum(value or 0 for value in prep)

    total_tasks = total_companies * 3

    if total_tasks == 0:
       overall_progress = 0
    else:
       overall_progress = round((completed_tasks / total_tasks) * 100)
    # Upcoming companies (nearest visit dates first)
    cursor.execute("""
    SELECT name, visit_date
    FROM companies
    WHERE user_id = ?
    ORDER BY visit_date ASC
    LIMIT 5
    """, (user_id,))

    upcoming_companies = cursor.fetchall()
    print(upcoming_companies)
    conn.close()

    return render_template(
        "dashboard.html",
        total_companies=total_companies,
        highest_package=highest_package,
        average_package=round(average_package, 2),
        overall_progress=overall_progress,
        upcoming_companies=upcoming_companies
    )

@app.route("/edit/<int:company_id>", methods=["GET", "POST"])
def edit_company(company_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()
    user_id = session["user_id"]

    if request.method == "POST":

        name = request.form["name"]
        role = request.form["role"]
        package = request.form["package"]
        visit_date = request.form["visit_date"]
        eligibility = request.form["eligibility"]

        cursor.execute("""
        UPDATE companies
        SET
            name=?,
            role=?,
            package=?,
            visit_date=?,
            eligibility=?
        WHERE id=? AND user_id=?
        """, (name, role, package, visit_date, eligibility, company_id, user_id))

        conn.commit()
        conn.close()

        return redirect("/companies")

    cursor.execute("""
    SELECT *
    FROM companies
    WHERE id=? AND user_id=?
    """, (company_id, user_id))

    company = cursor.fetchone()
    if company is None:
       conn.close()
       return "Access Denied!"

    conn.close()

    return render_template(
        "edit_company.html",
        company=company
    )

@app.route("/delete/<int:company_id>")
def delete_company(company_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()

    # Confirm this company belongs to the logged-in user before deleting anything
    cursor.execute(
        "SELECT id FROM companies WHERE id=? AND user_id=?",
        (company_id, user_id)
    )
    company = cursor.fetchone()
    if company is None:
        conn.close()
        return "Access Denied!"

    # Delete prep status first
    cursor.execute(
        "DELETE FROM prep_status WHERE company_id=?",
        (company_id,)
    )

    # Delete company
    cursor.execute(
        "DELETE FROM companies WHERE id=? AND user_id=?",
        (company_id, user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/companies")

@app.route("/send_reminder/<int:company_id>")
def send_company_reminder(company_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, role, package, visit_date
        FROM companies
        WHERE id=? AND user_id=?
    """, (company_id, user_id))

    company = cursor.fetchone()

    conn.close()

    if company is None:
        return "Access Denied!"

    # Change this to the email where you want reminders
    receiver_email = os.getenv("SENDER_EMAIL")

    send_reminder(
        receiver_email=receiver_email,
        company_name=company[0],
        role=company[1],
        package=company[2],
        visit_date=company[3]
    )

    return redirect("/companies")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        if not valid_password(password):

           return """
    Password must:
    <br>• Be exactly 8 characters
    <br>• Contain one uppercase letter
    <br>• Contain one lowercase letter
    <br>• Contain one digit
    <br>• Contain one special character
    """

        conn = sqlite3.connect("placement.db")
        cursor = conn.cursor()

        try:

            hashed_password = generate_password_hash(password)

            cursor.execute("""
INSERT INTO users(name,email,password)
VALUES(?,?,?)
""",(name,email,hashed_password))

            conn.commit()

            return redirect("/login")

        except sqlite3.IntegrityError:

            return "Email already exists!"

        finally:

            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("placement.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect("/dashboard")

        else:
            return "Invalid Email or Password!"

    return render_template("login.html")

@app.route("/logout")
def logout():

    session.clear()      # Remove all session data

    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)