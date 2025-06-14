
# Automated M&A Newsletter
## Features

- Scrapes top 10 M&A headlines from Reuters
- Ranks headlines based on M&A relevance
- Summarizes top 5 headlines using ChatGPT
- Sends beautifully formatted HTML emails
- Runs automatically on a daily schedule
- Web-based signup form for new subscribers
- Subscriber management system

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   RESEND_API_KEY=your_resend_api_key_here
   FROM_EMAIL=your_verified_sender_email@domain.com
   TO_EMAILS=recipient1@email.com,recipient2@email.com
   ```

4. Get your API keys:
   - OpenAI API key: https://platform.openai.com/api-keys
   - Resend API key: https://resend.com/api-keys

## Running the Application

1. Start the web server:
   ```bash
   python app.py
   ```
   This will start the Flask server on http://localhost:5000

2. Start the newsletter automation:
   ```bash
   python newsletter_automation.py
   ```

## Frontend

The frontend is a simple, responsive signup form built with HTML and Tailwind CSS. It's served directly by the Flask application and doesn't require any additional setup.

Features:
- Clean, modern design
- Mobile-responsive layout
- Form validation
- Success/error notifications
- Automatic subscriber management

## Subscriber Management

Subscribers are stored in a `subscribers.json` file, which is automatically updated when new users sign up. The newsletter system will automatically include new subscribers in the next email distribution.

## Requirements

- Python 3.7+
- Internet connection
- Valid API keys for OpenAI and Resend
- Verified sender email address in Resend

## Notes

- The script uses a keyword-based ranking system for headlines
- Email formatting is responsive and mobile-friendly
- The script includes error handling for API calls and web scraping
- Subscribers are automatically added to the mailing list
