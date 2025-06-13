import os
import requests
import feedparser
import openai
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json

# ── load environment variables ───────────────────────────
load_dotenv(dotenv_path=Path('.')/'.env')

EMAIL_SENDER      = os.getenv("EMAIL_SENDER")
EMAIL_RECIPIENTS  = os.getenv("EMAIL_RECIPIENTS", "")
RESEND_API_KEY    = os.getenv("RESEND_API_KEY")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")

names = ["EMAIL_SENDER", "RESEND_API_KEY", "OPENAI_API_KEY"]
missing_names = [names[i] for i, v in enumerate([EMAIL_SENDER, RESEND_API_KEY, OPENAI_API_KEY]) if not v]
if missing_names:
    raise RuntimeError("Missing required variables in .env: " + ", ".join(missing_names))

openai.api_key = OPENAI_API_KEY

# keyword exclude list
EXCLUDE_KEYWORDS = ['sports', 'science', 'lifestyle', 'pictures', 'graphics', 'entertainment', 'gaming']

RECENT_DAYS = 2
CUTOFF_DT = datetime.utcnow() - timedelta(days=RECENT_DAYS)

SUBSCRIBERS_FILE = 'subscribers.json'

def get_recipient_emails():
    emails = []
    if EMAIL_RECIPIENTS:
        emails.extend([e.strip() for e in EMAIL_RECIPIENTS.split(',') if e.strip()])
    # load subscribers file
    if Path(SUBSCRIBERS_FILE).exists():
        try:
            with open(SUBSCRIBERS_FILE, 'r') as f:
                subs = json.load(f)
                emails.extend([s['email'] for s in subs if 'email' in s])
        except Exception:
            pass
    # deduplicate while preserving order
    seen = set()
    unique = []
    for e in emails:
        if e not in seen:
            unique.append(e)
            seen.add(e)
    return unique

# --- 1A. Try Reuters RSS with headers ---
def fetch_reuters_rss():
    url = "https://feeds.reuters.com/reuters/mergersNews"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    feed = feedparser.parse(url, request_headers=headers)
    entries = [] if not feed.entries else feed.entries
    headlines = []
    for entry in entries[:15]:
        title_lower = entry.title.lower()
        if any(k in title_lower for k in EXCLUDE_KEYWORDS):
            continue
        if entry.published_parsed and entry.published_parsed > CUTOFF_DT:
            headlines.append({
                "title": entry.title,
                "link": entry.link,
                "summary": getattr(entry, 'summary', '')
            })
    return headlines

# --- 1B. Fallback HTML scraper ---

def fetch_reuters_html():
    url = "https://www.reuters.com/markets/deals/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("Error fetching HTML:", e)
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    cards = soup.find_all('div', attrs={'data-testid': 'MediaStoryCard'})
    headlines = []
    for card in cards[:20]:
        a_tag = card.find('a', attrs={'data-testid': 'Heading'})
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        if any(k in title.lower() for k in EXCLUDE_KEYWORDS):
            continue
        link = a_tag.get('href')
        if link and not link.startswith('http'):
            link = 'https://www.reuters.com' + link
        summary_tag = card.find('p')
        summary = summary_tag.get_text(strip=True) if summary_tag else ''
        headlines.append({"title": title, "link": link, "summary": summary})
    return headlines

# wrapper

def get_headlines():
    headlines = fetch_reuters_rss()
    if headlines:
        print("Fetched", len(headlines), "headlines from RSS")
        return headlines[:10]
    print("RSS empty, falling back to HTML scrape")
    headlines = fetch_reuters_html()
    print("Fetched", len(headlines), "headlines from HTML")
    return headlines[:10]

# --- 2. (Optional) Rank headlines ---
def rank_headlines(headlines):
    m_a_keywords = ['acquisition', 'merger', 'buyout', 'takeover', 'deal', 'M&A']
    ranked_headlines = []
    for headline in headlines:
        score = sum(1 for keyword in m_a_keywords if keyword.lower() in headline['title'].lower())
        ranked_headlines.append((headline, score))
    ranked_headlines.sort(key=lambda x: x[1], reverse=True)
    return [h[0] for h in ranked_headlines[:5]]  # Top 5

# --- 3. Summarize with OpenAI ---
def summarize_headlines(headlines):
    summaries = []
    for article in headlines:
        prompt = (
            f"Write a concise 5-7 sentence summary suitable for an M&A newsletter. including stats and numbers where applicable. "
            f"Focus on the companies involved, deal value (if mentioned), and strategic rationale.\n\n"
            f"Headline: {article['title']}\n"
            f"Extracted snippet: {article['summary']}\n"
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial news analyst specializing in M&A. Were providing a breif overview of a deal/decision in a newsletter summary. When you get the artcile produce a summary that covers what the deal/decision is, the context of the deal/decision in the space, the motivation behind the deal/decision for either company, and the potential impact of the deal/decision. Provide a 4-7 sentence summary for a newsletter."},
                    {"role": "user", "content": prompt}
                ]
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            summary = f"Error summarizing: {e}"
        summaries.append({
            "title": article["title"],
            "link": article["link"],
            "summary": summary
        })
    return summaries

# --- 4. Format HTML Email ---
def create_html_email(summaries):
    html_content = f"""
    <html>
    <body>
        <h1>M&A Newsletter</h1>
        <p>Here are today's top M&A headlines and summaries:</p>
    """
    for article in summaries:
        html_content += f"""
        <div style='margin-bottom:20px;'>
            <strong style="color:#000;font-weight:700;">{article['title']}</strong><br>
            <em>{article['summary']}</em><br>
            <a href="{article['link']}">Read more</a>
        </div>
        """
    html_content += "</body></html>"
    return html_content

# --- 5. Send Email via Resend ---
def send_email_via_resend(html_content, recipients=None):
    if recipients is None:
        recipients = get_recipient_emails()
    if not recipients:
        print("No recipients to send email to.")
        return None, None
    data = {
        "from": f"M&A Newsletter <{EMAIL_SENDER}>",
        "to": recipients,
        "subject": "M&A Deals – {}".format(datetime.utcnow().strftime('%b %d, %Y')),
        "html": html_content
    }
    print(f"📨 Sending to {len(recipients)} recipients via Resend…")
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json=data
    )
    print(f"📬 Resend Status: {response.status_code}")
    return response.status_code, response.text

# --- Main Workflow ---
def main():
    headlines = get_headlines()
    if not headlines:
        print("No headlines found")
        return
    ranked_headlines = rank_headlines(headlines)
    summaries = summarize_headlines(ranked_headlines)
    html_content = create_html_email(summaries)
    send_email_via_resend(html_content)

if __name__ == "__main__":
    main() 

