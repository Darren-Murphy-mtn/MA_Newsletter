from flask import Flask, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='frontend')

# File to store subscribers
SUBSCRIBERS_FILE = 'subscribers.json'

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(subscribers, f)

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    
    if not email or not name:
        return jsonify({'error': 'Email and name are required'}), 400
    
    subscribers = load_subscribers()
    
    # Check if email already exists
    if any(sub['email'] == email for sub in subscribers):
        return jsonify({'error': 'This email is already subscribed to the newsletter'}), 400
    
    # Add new subscriber
    subscribers.append({
        'email': email,
        'name': name,
        'subscribed_at': str(datetime.now())
    })
    
    save_subscribers(subscribers)
    
    # Update the TO_EMAILS environment variable
    current_emails = os.getenv('TO_EMAILS', '').split(',')
    if email not in current_emails:
        current_emails.append(email)
        os.environ['TO_EMAILS'] = ','.join(filter(None, current_emails))
    
    return jsonify({'message': 'Successfully subscribed'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 

def send_test_email():
    from datetime import datetime
    html_content = f"""
    <html>
    <body>
        <h1>Test M&A Newsletter</h1>
        <p>This is a test email sent at {datetime.now()}.</p>
    </body>
    </html>
    """
    try:
        email_data = {
            "from": os.getenv('FROM_EMAIL'),
            "to": os.getenv('TO_EMAILS').split(','),
            "subject": f"Test M&A Newsletter - {datetime.now().strftime('%B %d, %Y')}",
            "html": html_content
        }
        response = resend.send_email(**email_data)
        print("Resend API response:", response)
    except Exception as e:
        print(f"Error sending test email: {e}")

if __name__ == "__main__":
    send_test_email()