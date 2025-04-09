"""Email templates for the safety observation application."""

def get_observation_email_template(employee_name, observation_data):
    """
    Generate an HTML email template for safety observation notification.
    
    Args:
        employee_name (str): The name of the employee
        observation_data (dict): Dictionary containing observation details
        
    Returns:
        str: HTML formatted email content
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #333333;
                line-height: 1.6;
            }}
            .container {{
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
            }}
            .header {{
                background-color: #0056d2;
                color: white;
                padding: 15px 25px;
                text-align: center;
                border-radius: 5px 5px 0 0;
            }}
            .content {{
                padding: 20px 25px;
                background-color: #f7f9fc;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 10px 15px;
                border: 1px solid #ddd;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .footer {{
                padding: 15px 25px;
                text-align: center;
                font-size: 12px;
                color: #666;
                background-color: #f2f2f2;
                border-radius: 0 0 5px 5px;
            }}
            .highlight {{
                font-weight: bold;
                color: {observation_data.get('overall_act') == 'Unsafe Act' and '#dc3545' or '#28a745'};
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Safety Observation Notification</h2>
            </div>
            <div class="content">
                <p>A safety observation has been submitted for <strong>{employee_name}</strong>.</p>
                
                <table>
                    <tr>
                        <th>Field</th>
                        <th>Details</th>
                    </tr>
                    <tr>
                        <td>Company</td>
                        <td>{observation_data.get('company', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Employee</td>
                        <td>{employee_name}</td>
                    </tr>
                    <tr>
                        <td>Overall Act</td>
                        <td class="highlight">{observation_data.get('overall_act', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Location</td>
                        <td>{observation_data.get('location', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Area Observed</td>
                        <td>{observation_data.get('area_observed', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Date Observed</td>
                        <td>{observation_data.get('date_observed', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td>Observation</td>
                        <td>{observation_data.get('observation', 'N/A')}</td>
                    </tr>
                </table>
                
                <p>Please review this safety observation and take appropriate action if necessary.</p>
            </div>
            <div class="footer">
                <p>This is an automated message from the Safety Observation System. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

def get_plain_text_template(employee_name, observation_data):
    """
    Generate a plain text email template for safety observation notification.
    
    Args:
        employee_name (str): The name of the employee
        observation_data (dict): Dictionary containing observation details
        
    Returns:
        str: Plain text formatted email content
    """
    text_content = f"""
SAFETY OBSERVATION NOTIFICATION

A safety observation has been submitted by {employee_name}.

OBSERVATION DETAILS:
-------------------
Company: {observation_data.get('company', 'N/A')}
Employee: {employee_name}
Overall Act: {observation_data.get('overall_act', 'N/A')}
Location: {observation_data.get('location', 'N/A')}
Area Observed: {observation_data.get('area_observed', 'N/A')}
Date Observed: {observation_data.get('date_observed', 'N/A')}

Observation:
{observation_data.get('observation', 'N/A')}

Please review this safety observation and take appropriate action if necessary.

-------------------
This is an automated message from the Safety Observation System. Please do not reply to this email.
"""
    return text_content