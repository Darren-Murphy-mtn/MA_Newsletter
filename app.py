from flask import Flask, request, jsonify, send_from_directory
from markupsafe import Markup
import os
from dotenv import load_dotenv
import json
from pathlib import Path
from datetime import datetime
import re
from functools import wraps
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
from supabase import create_client, Client
import uuid
# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

DATABASE_URL = os.getenv('DATABASE_URL')

# Helper to get DB connection
def get_db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def load_subscribers():
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT email, name, subscribed_at, token FROM subscribers')
            return cur.fetchall()

def save_subscriber(email, name, token):
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO subscribers (email, name, token) VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING', (email, name, token))
            conn.commit()

def remove_subscriber(email, token):
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM subscribers WHERE email=%s AND token=%s', (email, token))
            conn.commit()

def is_valid_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)

def is_valid_name(name):
    return bool(name) and len(name) <= 100 and re.match(r"^[\w .'-]+$", name)

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

    # Check if already subscribed
    existing = supabase.table("subscribers").select("email").eq("email", email).execute()
    if existing.data:
        return jsonify({'error': 'This email is already subscribed to the newsletter'}), 400

    unsubscribe_token = str(uuid.uuid4())
    try:
        result = supabase.table("subscribers").insert({
            "email": email,
            "name": name,
            "unsubscribe_token": unsubscribe_token,
            "unsubscribed": False
        }).execute()
        if result.error:
            print("Supabase error:", result.error)
            return jsonify({'error': str(result.error)}), 500

        # Send confirmation email
        send_test_email(email, unsubscribe_token)

        return jsonify({'message': 'Successfully subscribed'}), 200
    except Exception as e:
        print("Exception:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/admin/subscribers', methods=['GET'])
def list_subscribers():
    token = request.args.get('token')
    if token != os.getenv('ADMIN_TOKEN'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(load_subscribers())

@app.route('/unsubscribe', methods=['GET'])
def unsubscribe():
    email = request.args.get('email')
    token = request.args.get('token')
    if not email or not token:
        return "Invalid unsubscribe link.", 400
    remove_subscriber(email, token)
    return Markup(f"You have been unsubscribed: {email}")

def send_test_email(to_email, unsubscribe_token):
    html_content = f"""
    <html>
    <body>
        <h1>M&amp;A Newsletter</h1>
        <p>You've subscribed to the M&amp;A Newsletter.</p>
        <a href=\"https://manewsletter-production.up.railway.app/unsubscribe?email={to_email}&token={unsubscribe_token}\">Unsubscribe</a>
    </body>
    </html>
    """
    try:
        email_data = {
            "from": os.getenv('FROM_EMAIL'),
            "to": [to_email],
            "subject": "M&A Newsletter Subscription Confirmation",
            "html": html_content
        }
        response = resend.send_email(**email_data)
        print("Resend API response:", response)
    except Exception as e:
        print(f"Error sending confirmation email: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)