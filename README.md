# Python_projects
#first working on the basics
# 
# Automated M&A Newsletter

This project creates an automated newsletter that scrapes M&A headlines from Reuters, ranks them, summarizes them using ChatGPT, and sends them via email using Resend. It also includes a web-based signup form for new subscribers.

## Features

- Scrapes top 10 M&A headlines from Reuters
- Ranks headlines based on M&A relevance using scoring function
- Summarizes top 5 headlines using ChatGPT
- Sends (hopefully) beautifully formatted HTML emails
- Runs automatically on a daily schedule
- Web-based signup form for new subscribers
- Subscriber management system using JSON

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

- The script uses a simple keyword-based ranking system for headlines
- Email formatting is responsive and mobile-friendly
- The script includes error handling for API calls and web scraping
- Subscribers are automatically added to the mailing list
