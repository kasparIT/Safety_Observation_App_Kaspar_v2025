from flask import Blueprint, render_template, request, jsonify, g, redirect, url_for, session, flash
from app.database import get_db_connection, get_companies
from datetime import datetime
import smtplib
import os
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Create utils directory if it doesn't exist
utils_dir = os.path.join(os.path.dirname(__file__), '..', 'utils')
if not os.path.exists(utils_dir):
    os.makedirs(utils_dir)
    # Create an __init__.py file to make it a package
    with open(os.path.join(utils_dir, '__init__.py'), 'w') as f:
        f.write('# Utils package\n')

# Import email templates
try:
    from app.utils.email_templates import get_observation_email_template, get_plain_text_template
except ImportError:
    # Define error handling if the module can't be imported
    print("Error importing email templates. Using default templates.")
    
    def get_observation_email_template(employee_name, observation_data):
        return f"<html><body><p>Safety observation for {employee_name}</p></body></html>"
    
    def get_plain_text_template(employee_name, observation_data):
        return f"Safety observation for {employee_name}"

load_dotenv()
EMAINT_URL = os.getenv("EMAINT_URL")

main = Blueprint("main", __name__)

# Company name mapping moved to global scope for access by database.py
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
    # Get companies with improved connection handling
    companies = get_companies()
    
    # Check if there's a successful submission in session
    if 'success_data' in session:
        success_data = session.pop('success_data')
        return render_template("index.html", 
                               companies=companies, 
                               success_msg=success_data.get('success_msg'),
                               emaint_url=EMAINT_URL,
                               employee_name=success_data.get('employee_name'),
                               employee_id=success_data.get('employee_id'),
                               observation_data=success_data.get('observation_data'))
    
    if request.method == "POST":
        company = request.form.get("company")
        employee_id = request.form.get("employee")
        overall_act = request.form.get("overall_act")
        location = request.form.get("location")
        area = request.form.get("area_observed")
        observation = request.form.get("observation")
        date_observed = request.form.get("date")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Keep form data to maintain state if validation fails
        form_data = {
            "company": company,
            "employee_id": employee_id,
            "overall_act": overall_act,
            "location": location,
            "area_observed": area,
            "observation": observation,
            "date_observed": date_observed
        }

        if not all([company, employee_id, overall_act, location, area, observation, date_observed]):
            error_msg = f"All fields are required. ({timestamp})"
            
            # Get employee name for form preservation
            employee_name = None
            if employee_id:
                with get_db_connection() as conn:
                    if conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                SELECT First_Name, Middle_Name, Last_Name
                                FROM dbo.Paylocity_Employee_Data
                                WHERE Employee_Id = ?
                            """, (employee_id,))
                            row = cursor.fetchone()
                            if row:
                                first, middle, last = row
                                employee_name = f"{first} {middle + ' ' if middle else ''}{last}"
                        finally:
                            cursor.close()
            
            return render_template("index.html", companies=companies, error_msg=error_msg,
                                  form_data=form_data, employee_name=employee_name)

        try:
            employee_name = None
            with get_db_connection() as conn:
                if not conn:
                    raise Exception("Failed to connect to database")
                
                cursor = conn.cursor()
                try:
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
                finally:
                    cursor.close()

            # Store observation data for use in templates
            observation_data = {
                "company": company,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "overall_act": overall_act,
                "location": location,
                "area_observed": area,
                "observation": observation,
                "date_observed": date_observed
            }
            
            success_msg = f"Submission successful at {timestamp}"
            
            # Store success data in session and redirect
            session['success_data'] = {
                'success_msg': success_msg,
                'employee_name': employee_name,
                'employee_id': employee_id,
                'observation_data': observation_data
            }
            
            # Redirect to GET request to prevent form resubmission
            return redirect(url_for('main.home'))

        except Exception as e:
            print(f"❌ Error inserting submission: {e}")
            error_msg = f"Submission failed at {timestamp}"
            return render_template("index.html", companies=companies, error_msg=error_msg, form_data=form_data)

    return render_template("index.html", companies=companies)

@main.route("/get-employees", methods=["POST"])
def get_employees():
    data = request.json
    selected_company = data.get("company")
    employees = []

    with get_db_connection() as conn:
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

    return jsonify(employees)


@main.route("/notify-supervisor", methods=["POST"])
def notify_supervisor():
    print("🔔 Received notify-supervisor request")
    
    # Get employee_id and observation data from form data
    employee_id = request.form.get("employee_id")
    print(f"📥 employee_id received: {employee_id}")
    
    if not employee_id:
        print("❌ Missing employee_id in request")
        return jsonify({"success": False, "error": "Missing employee_id"}), 400

    with get_db_connection() as conn:
        if not conn:
            print("❌ Failed to connect to database")
            return jsonify({"success": False, "error": "Database connection failed"}), 500
            
        cursor = conn.cursor()
        try:
            # Get employee details and supervisor email
            cursor.execute("""
                SELECT e.Supervisor_Work_Email, e.First_Name, e.Middle_Name, e.Last_Name,
                       s.First_Name, s.Last_Name
                FROM dbo.Paylocity_Employee_Data e
                LEFT JOIN dbo.Paylocity_Employee_Data s ON e.Supervisor_Employee_Id = s.Employee_Id
                WHERE e.Employee_Id = ?
            """, (employee_id,))
            row = cursor.fetchone()
            print(f"🧠 DB Lookup result: {row}")
            
            if not row:
                print(f"❌ Employee not found: {employee_id}")
                return jsonify({"success": False, "error": "Employee not found"}), 404
                
            supervisor_email, first, middle, last, supervisor_first, supervisor_last = row if len(row) == 6 else (row[0], row[1], row[2], row[3], None, None)
            employee_name = f"{first} {middle + ' ' if middle else ''}{last}"
            
            if not supervisor_email:
                print(f"❌ No supervisor email found for employee ID: {employee_id}")
                return jsonify({"success": False, "error": "No supervisor email found for this employee"}), 404

            # Get the observation details
            cursor.execute("""
                SELECT company, overall_act, location, area_observed, observation, date_observed
                FROM dbo.SafetyObservationsApp_Revamp
                WHERE employee_id = ?
                ORDER BY id DESC
            """, (employee_id,))
            
            obs_row = cursor.fetchone()
            if not obs_row:
                print(f"❌ No observation found for employee ID: {employee_id}")
                return jsonify({"success": False, "error": "No observation found for this employee"}), 404
                
            company, overall_act, location, area_observed, observation, date_observed = obs_row
            
            # Create observation data dict for email template
            observation_data = {
                "company": company,
                "employee_id": employee_id,
                "employee_name": employee_name,
                "overall_act": overall_act,
                "location": location,
                "area_observed": area_observed,
                "observation": observation,
                "date_observed": date_observed
            }

            # Setup email message (multipart for HTML and plain text)
            msg = MIMEMultipart("alternative")
            supervisor_name = f"{supervisor_first} {supervisor_last}" if supervisor_first and supervisor_last else "Supervisor"
            msg["Subject"] = f"Safety Observation for {employee_name}"
            msg["From"] = os.getenv("EMAIL_USERNAME")
            msg["To"] = supervisor_email
            
            # Plain text version
            text_content = get_plain_text_template(employee_name, observation_data)
            part1 = MIMEText(text_content, "plain")
            
            # HTML version
            html_content = get_observation_email_template(employee_name, observation_data)
            part2 = MIMEText(html_content, "html")
            
            # Attach parts - the last part is preferred by email clients
            msg.attach(part1)
            msg.attach(part2)

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

            return jsonify({"success": True, "message": f"Email sent to {supervisor_name}"})
        except Exception as e:
            print(f"❌ Error in notify_supervisor: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
        finally:
            cursor.close()