from flask import Blueprint, render_template, request, jsonify
from app.database import get_db_connection

main = Blueprint("main", __name__)

@main.route("/")
def home():
    """Fetch unique company names for dropdown."""
    conn = get_db_connection()
    companies = []

    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT Company_Name FROM dbo.Paylocity_Employee_Data WHERE Company_Name IS NOT NULL")
            companies = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error fetching companies: {e}")
        finally:
            conn.close()

    return render_template("index.html", companies=companies)


@main.route("/get-employees", methods=["POST"])
def get_employees():
    """Fetch employees for the selected company."""
    data = request.json
    selected_company = data.get("company")  # Get selected company from request

    conn = get_db_connection()
    employees = []

    if conn:
        cursor = conn.cursor()
        try:
            # Fetch employees for the selected company and order alphabetically
            cursor.execute("""
                SELECT Employee_Id, First_Name, Middle_Name, Last_Name 
                FROM dbo.Paylocity_Employee_Data 
                WHERE Company_Name = ? AND First_Name IS NOT NULL AND Last_Name IS NOT NULL
                ORDER BY First_Name ASC
            """, (selected_company,))
            
            employees = [
                {"id": row[0], "name": f"{row[1]} {row[2]+' ' if row[2] else ''}{row[3]}"}
                for row in cursor.fetchall()
            ]
        except Exception as e:
            print(f"❌ Error fetching employees: {e}")
        finally:
            conn.close()

    return jsonify(employees)  # Return employees as JSON
