
from flask import Blueprint, render_template, request, jsonify, redirect
from app.database import get_db_connection

main = Blueprint("main", __name__)

COMPANY_NAME_MAPPING = {
    "HFA": "HFA - Horizon Firearms",
    "KCI": "KCI - Kaspar Companies Inc.",
    "KPI": "KPI - Kaspar Property",
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

        if not all([company, employee_id, overall_act, location, area, observation, date_observed]):
            return "All fields are required", 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Lookup employee name
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

            # Insert into the table
            cursor.execute("""
                INSERT INTO dbo.SafetyObservationsApp_Revamp
                (company, employee_id, employee_name, overall_act, location, area_observed, observation, date_observed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (company, employee_id, employee_name, overall_act, location, area, observation, date_observed))
            conn.commit()
        except Exception as e:
            print(f"❌ Error inserting submission: {e}")
            return "Database error", 500
        finally:
            cursor.close()
            conn.close()

        return redirect("/")

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
