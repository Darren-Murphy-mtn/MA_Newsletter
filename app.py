from flask import Flask, request, jsonify, send_from_directory, Markup
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime
import re
from functools import wraps
import time

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='frontend')

# File to store subscribers
SUBSCRIBERS_FILE = 'subscribers.json'

# Simple in-memory rate limiter (per IP, per minute)
rate_limit = {}
def rate_limited(limit=5, per=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            if ip not in rate_limit:
                rate_limit[ip] = []
            # Remove timestamps older than 'per' seconds
            rate_limit[ip] = [t for t in rate_limit[ip] if now - t < per]
            if len(rate_limit[ip]) >= limit:
                return jsonify({'error': 'Too many requests, slow down!'}), 429
            rate_limit[ip].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(subscribers, f)

def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)

def is_valid_name(name):
    return bool(name) and len(name) <= 100 and re.match(r"^[\w .'-]+$", name)

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/api/subscribe', methods=['POST'])
@rate_limited(limit=5, per=60)
def subscribe():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    if not email or not name:
        return jsonify({'error': 'Email and name are required'}), 400
    if not is_valid_email(email):
        return jsonify({'error': 'Invalid email address'}), 400
    if not is_valid_name(name):
        return jsonify({'error': 'Invalid name'}), 400
    subscribers = load_subscribers()
    if any(sub['email'] == email for sub in subscribers):
        return jsonify({'error': 'This email is already subscribed to the newsletter'}), 400
    import secrets
    token = secrets.token_urlsafe(16)
    subscribers.append({
        'email': email,
        'name': name,
        'subscribed_at': str(datetime.now()),
        'token': token
    })
    save_subscribers(subscribers)
    # Update the TO_EMAILS environment variable
    current_emails = os.getenv('TO_EMAILS', '').split(',')
    if email not in current_emails:
        current_emails.append(email)
        os.environ['TO_EMAILS'] = ','.join(filter(None, current_emails))
    return jsonify({'message': 'Successfully subscribed'}), 200

@app.route('/admin/subscribers', methods=['GET'])
def list_subscribers():
    token = request.args.get('token')
    if token != os.getenv('ADMIN_TOKEN'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not os.path.exists(SUBSCRIBERS_FILE):
        return jsonify([])
    with open(SUBSCRIBERS_FILE, 'r') as f:
        return jsonify(json.load(f))

@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    email = request.args.get('email')
    token = request.args.get('token')
    if not email or not token:
        return "Invalid unsubscribe link.", 400
    subscribers = load_subscribers()
    new_subs = [s for s in subscribers if not (s['email'] == email and s.get('token') == token)]
    if len(new_subs) == len(subscribers):
        return "Invalid or already unsubscribed.", 400
    save_subscribers(new_subs)
    return Markup(f"You have been unsubscribed: {email}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 

def send_test_email():
    from datetime import datetime
    html_content = f"""
    <html>
    <body>
        <h1>Test M&A Newsletter</h1>
        <p>This is a test email sent at {datetime.now()}.</p>
        <a href="https://your-app.onrender.com/unsubscribe?email={article['email']}">Unsubscribe</a>
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