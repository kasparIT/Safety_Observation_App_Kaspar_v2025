from flask import Blueprint, render_template, request, jsonify
from app.database import get_db_connection
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()
EMAINT_URL = os.getenv("EMAINT_URL")


main = Blueprint("main", __name__)

COMPANY_NAME_MAPPING = {
    "HFA": "HFA - Kaspar Outdoors",
    "KCI": "KCI - Kaspar Companies Inc.",
    "KPI": "KPI - Kaspar Properties",
    "TA": "TA - Texas Ammunition",
    "TBE": "TBE - Bedrock Truck Beds",
    "TPM": "TPM - Texas Precious Metals",
    "TRK": "TRK - Kaspar Trucking",
    "WHL": "WHL - Circle Y Saddles & Precision Saddle Tree"
}

@main.route("/", methods=["GET", "POST"])
def home():
    conn = get_db_connection()
    companies = []

    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT Company_Name FROM dbo.Paylocity_Employee_Data WHERE Company_Name IS NOT NULL")
            fetched_companies = [row[0] for row in cursor.fetchall()]
            companies = [(abbr, COMPANY_NAME_MAPPING.get(abbr, abbr)) for abbr in fetched_companies]
        finally:
            cursor.close()

    if request.method == "POST":
        company = request.form.get("company")
        employee_id = request.form.get("employee")
        overall_act = request.form.get("overall_act")
        location = request.form.get("location")
        area = request.form.get("area_observed")
        observation = request.form.get("observation")
        date_observed = request.form.get("date")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if not all([company, employee_id, overall_act, location, area, observation, date_observed]):
            error_msg = f"All fields are required. ({timestamp})"
            return render_template("index.html", companies=companies, error_msg=error_msg)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT First_Name, Middle_Name, Last_Name
                FROM dbo.Paylocity_Employee_Data
                WHERE Employee_Id = ?
            """, (employee_id,))
            row = cursor.fetchone()
            if row:
                first, middle, last = row
                employee_name = f"{first} {middle + ' ' if middle else ''}{last}"
            else:
                employee_name = "Unknown"

            cursor.execute("""
                INSERT INTO dbo.SafetyObservationsApp_Revamp
                (company, employee_id, employee_name, overall_act, location, area_observed, observation, date_observed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (company, employee_id, employee_name, overall_act, location, area, observation, date_observed))
            conn.commit()

            success_msg = f"Submission successful at {timestamp}"
            return render_template("index.html", companies=companies, success_msg=success_msg, 
                                  emaint_url=EMAINT_URL, employee_name=employee_name, employee_id=employee_id)

        except Exception as e:
            print(f"❌ Error inserting submission: {e}")
            error_msg = f"Submission failed at {timestamp}"
            return render_template("index.html", companies=companies, error_msg=error_msg)
        finally:
            cursor.close()
            conn.close()

    if conn:
        conn.close()

    return render_template("index.html", companies=companies)

@main.route("/get-employees", methods=["POST"])
def get_employees():
    data = request.json
    selected_company = data.get("company")
    conn = get_db_connection()
    employees = []

    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT Employee_Id, First_Name, Middle_Name, Last_Name 
                FROM dbo.Paylocity_Employee_Data 
                WHERE Company_Name = ? AND Is_Active = 'Yes' AND First_Name IS NOT NULL AND Last_Name IS NOT NULL
                ORDER BY First_Name ASC
            """, (selected_company,))
            employees = [
                {"id": row[0], "name": f"{row[1]} {row[2]+' ' if row[2] else ''}{row[3]}"}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"❌ Error fetching employees: {e}")
        finally:
            cursor.close()
            conn.close()

    return jsonify(employees)


@main.route("/notify-supervisor", methods=["POST"])
def notify_supervisor():
    print("🔔 Received notify-supervisor request")
    
    # Get employee_id from form data
    employee_id = request.form.get("employee_id")
    print(f"📥 employee_id received: {employee_id}")
    
    if not employee_id:
        print("❌ Missing employee_id in request")
        return jsonify({"success": False, "error": "Missing employee_id"}), 400

    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return jsonify({"success": False, "error": "Database connection failed"}), 500
        
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Supervisor_Work_Email, First_Name, Last_Name FROM dbo.Paylocity_Employee_Data WHERE Employee_Id = ?", (employee_id,))
        row = cursor.fetchone()
        print(f"🧠 DB Lookup result: {row}")
        
        if not row or not row[0]:
            print(f"❌ No supervisor email found for employee ID: {employee_id}")
            return jsonify({"success": False, "error": "No supervisor email found"}), 404

        supervisor_email, first, last = row
        employee_name = f"{first} {last}"

        # Setup email message
        msg = EmailMessage()
        msg["Subject"] = f"New Safety Observation for {employee_name}"
        msg["From"] = os.getenv("EMAIL_USERNAME")
        msg["To"] = supervisor_email
        msg.set_content(f"A safety observation was submitted for {employee_name}. Please check the system for full details.")

        # Send email
        try:
            with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT", 587))) as smtp:
                smtp.starttls()
                smtp.login(os.getenv("EMAIL_USERNAME"), os.getenv("EMAIL_PASSWORD"))
                print(f"📧 Sending email to {supervisor_email}...")
                smtp.send_message(msg)
                print("✅ Email sent successfully")
        except Exception as email_error:
            print(f"❌ Email sending failed: {email_error}")
            return jsonify({"success": False, "error": str(email_error)}), 500

        return jsonify({"success": True})
    except Exception as e:
        print(f"❌ Error in notify_supervisor: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()