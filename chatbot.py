from flask import Flask, request, jsonify
from flask_cors import CORS
from simple_salesforce import Salesforce
import re

app = Flask(__name__)
CORS(app)

# Salesforce authentication details
USERNAME = 'rahulfatnani9@mindful-narwhal-38mkxl.com'
PASSWORD = 'Rahul@1234'
SECURITY_TOKEN = '91GtNAAHM6k43yrmIIPSv9G1'
DOMAIN = 'login'  # Use 'test' for sandbox or 'login' for production

def authenticate_salesforce():
    """Authenticate with Salesforce."""
    try:
        sf = Salesforce(
            username=USERNAME,
            password=PASSWORD,
            security_token=SECURITY_TOKEN,
            domain=DOMAIN
        )
        return sf
    except Exception as e:
        print(f"Salesforce authentication failed: {str(e)}")
        return None

def extract_case_number(user_message):
    """
    Try to find a case number within a user message using a pattern.
    """
    match = re.search(r'\b\d{5,}\b', user_message)
    if match:
        return match.group(0)
    return None

@app.route('/initialize', methods=['GET'])
def initialize():
    response = {
        "message": "Hello, I am SGChatBot. Your Virtual Assistant. Greetings of the day!",
        "buttons": [
            {"text": "Products and Solutions", "payload": "products_solutions"},
            {"text": "Create a Case", "payload": "case_creation"},
            {"text": "Case Status", "payload": "case_status"}
        ]
    }
    return jsonify(response)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip().lower()
    context = request.json.get('context', {})

    # Debugging: log received user message and context
    print(f"Received user message: '{user_message}'")
    print(f"Received context: {context}")

    # Authenticate with Salesforce
    sf = authenticate_salesforce()
    if sf is None:
        return jsonify({"error": "Salesforce authentication failed"}), 500

    # If the bot is waiting for a case number, try to extract the case number
    if context.get('waiting_for_case_number', False):
        case_number = extract_case_number(user_message)
        print(f"Extracted Case Number: '{case_number}'")  # Debugging print
        if case_number:
            try:
                query_result = sf.query(f"SELECT Status FROM Case WHERE CaseNumber = '{case_number}'")
                print(f"Salesforce Query Result: {query_result}")  # Debugging print
                cases = query_result.get('records', [])
                if cases:
                    return jsonify({
                        "message": f"Case Status: {cases[0]['Status']}",
                        "context": {}
                    })
                else:
                    return jsonify({
                        "message": f"No case found with the case number {case_number}.",
                        "context": {}
                    })
            except Exception as e:
                print(f"Salesforce query failed: {str(e)}")  # Debugging print
                return jsonify({
                    "error": f"Salesforce query failed: {str(e)}"
                }), 500
        else:
            return jsonify({
                "message": "Please provide a valid case number.",
                "context": {"waiting_for_case_number": True}
            })

    # Handle "case status" request
    if user_message == "case_status":
        return jsonify({
            "message": "Please provide the case number for which you want to know the status.",
            "context": {"waiting_for_case_number": True}
        })

    # Default fallback response
    return jsonify({
        "message": "Sorry, I couldn't understand your request. Please provide a case number or ask about case status.",
        "context": {}
    })

if __name__ == '__main__':
    app.run(debug=True)
