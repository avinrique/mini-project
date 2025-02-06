
import flask
from flask import request, jsonify
import google.generativeai as genai
import asyncio
import concurrent.futures
from reportlab.pdfgen import canvas
import os
from datetime import datetime
from fpdf import FPDF
import markdown2
import pdfkit
config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
# Configure the Gemini API
genai.configure(api_key="AIzaSyD02mt7Sejc3Ky6G7te8adqlk5BQr1ekj8")

# Initialize the vulnerability checking model
model_vulnerability_checker = genai.GenerativeModel("gemini-pro")

# Examples of vulnerable and secure code
vulnerability_examples = """
### Vulnerable Code Example 1:
def login(user_input):
    query = "SELECT * FROM users WHERE username = '" + user_input + "';"
    execute_query(query)

### Secure Code Example 1:
def login(user_input):
    query = "SELECT * FROM users WHERE username = ?;"
    execute_query_with_params(query, (user_input,))

### Vulnerable Code Example 2:
import os
os.system("rm -rf /")

### Secure Code Example 2:
import os
if safe_condition:
    os.system("rm -rf /home/safe_directory")

### Vulnerable Code Example 3:
data = "<script>alert('XSS')</script>"
response.write(data)

### Secure Code Example 3:
data = "<script>alert('XSS')</script>"
safe_data = escape(data)
response.write(safe_data)

### Vulnerable Code Example 4:
def insecure_function(password):
    if password == "12345":
        return True

### Secure Code Example 4:
def secure_function(password):
    hashed_password = hash_password(password)
    if hashed_password == stored_hashed_password:
        return True

### Vulnerable Code Example 5:
file = open("data.txt", "r")
file.read()

### Secure Code Example 5:
with open("data.txt", "r") as file:
    file.read()
"""
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)
# Create a Flask application
app = flask.Flask(__name__)

def analyze_code_vulnerabilities(code):
    """Analyze the provided code for vulnerabilities using the Gemini model."""

    try:
        prompt = (
            f"Analyze the following Python code for vulnerabilities. "
            f"Just Provide a response on whivh code the code is vulnerable exactly and what it is vulnerable to  with line numbers"
            f"and include suggestions for improvement if it's vulnerable. or give the secure code for this "
            f"Here are some examples for reference:\n{vulnerability_examples}\n\n"
            f"Code to analyze:\n{code}"
        )
        
        response = model_vulnerability_checker.generate_content(prompt, safety_settings={
        'HARASSMENT': 'block_none',
        'HATE_SPEECH': 'block_none',
        'HARM_CATEGORY_HARASSMENT': 'block_none',
        'HARM_CATEGORY_HATE_SPEECH': 'block_none',
        'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
        'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none',
    })
      
        return response.text
    except Exception as e:
        return f"Error during vulnerability analysis: {e}"
@app.route("/report", methods=["POST"])

# Path to wkhtmltopdf (you may need to install it first)


# Configure pdfkit to use the correct path




def generate_report():
    """Generate a detailed security report for the organization based on the code and its vulnerability analysis."""
    user_code = request.json.get("code")
    linting_comments = request.json.get("code_sum")

    if not user_code or not linting_comments:
        return jsonify({"error": "No code or analysis result provided"}), 400

    try:
        # Prepare the prompt for Gemini to generate the report
        prompt = (
            f"Create a detailed security report for the organization based on the following code analysis:\n\n"
            f"Code:\n{user_code}\n\n"
            f"Analysis (Vulnerabilities and suggestions):\n{linting_comments}\n\n"
            "Provide a detailed report with the following sections:\n"
            "1. Overview of the code and vulnerabilities.\n"
            "2. Detailed vulnerability findings with line numbers.\n"
            "3. Suggested improvements and secure code examples.\n"
            "4. General security best practices.\n"
            "The report should be in a professional tone and easy to read."
        )

        # Call Gemini to generate the report
        response = model_vulnerability_checker.generate_content(prompt, safety_settings={
            'HARASSMENT': 'block_none',
            'HATE_SPEECH': 'block_none',
            'HARM_CATEGORY_HARASSMENT': 'block_none',
            'HARM_CATEGORY_HATE_SPEECH': 'block_none',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'block_none',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'block_none',
        })

        # Generate file names
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_filename = f"security_report_{timestamp}.md"
        html_filename = f"security_report_{timestamp}.html"
        pdf_filename = f"security_report_{timestamp}.pdf"
        reports_dir = 'reports'

        # Ensure reports directory exists
        os.makedirs(reports_dir, exist_ok=True)

        # Save report as Markdown file
        md_filepath = os.path.join(reports_dir, md_filename)
        with open(md_filepath, 'w', encoding='utf-8') as md_file:
            md_file.write(response.text)

        # Convert Markdown to HTML
        html_content = markdown2.markdown(response.text)

        # Add some basic styling
        styled_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                pre {{ background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                code {{ font-family: monospace; font-size: 14px; }}
            </style>
        </head>
        <body>
            <h1>Security Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            {html_content}
        </body>
        </html>
        """

        # Save HTML file
        html_filepath = os.path.join(reports_dir, html_filename)
        with open(html_filepath, 'w', encoding='utf-8') as html_file:
            html_file.write(styled_html)

        # Convert HTML to PDF
        pdf_filepath = os.path.join(reports_dir, pdf_filename)
        pdfkit.from_file(html_filepath, pdf_filepath, configuration=config)

        # Return the path to the generated PDF file
        return jsonify({"report_location": pdf_filepath})

    except Exception as e:
        return jsonify({"error": f"Error generating report: {e}"}), 500
@app.route("/analyze", methods=["POST"])
def analyze():
    """API endpoint to analyze posted code."""
    user_code = request.json.get("code")

    
    if not user_code:
        return jsonify({"error": "No code provided"}), 400
    
    # Asynchronously process the code vulnerability analysis
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(analyze_code_vulnerabilities, user_code)
        result = future.result()

    return jsonify({"analysis_result": result})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
