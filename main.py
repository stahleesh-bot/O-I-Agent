import pandas as pd
import random
from datetime import datetime
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
import os

CSV_FILE = "data.csv"
LOG_FILE = "logs.csv"

FORM_URL = "https://example.com/form"  # <-- replace with your real form URL

EMAIL_FROM = "yourgmail@gmail.com"
EMAIL_TO = "yourgmail@gmail.com"
EMAIL_PASS = os.environ.get("EMAIL_PASS")  # GitHub secret

# -------------------------

df = pd.read_csv(CSV_FILE)
rows_total = len(df)

selected = df.sample(21)  # pick 21 random rows
submitted = 0

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for _, row in selected.iterrows():
        page.goto(FORM_URL)

        page.fill("input[name='name']", row["name"])
        page.fill("input[name='email']", row["email"])
        page.fill("input[name='phone']", str(row["phone"]))
        page.fill("input[name='city']", row["city"])

        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

        submitted += 1

    browser.close()

# ---------- LOGGING ----------

now = datetime.now()

log_entry = {
    "date": now.strftime("%Y-%m-%d"),
    "time": now.strftime("%H:%M"),
    "total_rows": rows_total,
    "submitted_rows": submitted
}

try:
    logs = pd.read_csv(LOG_FILE)
    logs = pd.concat([logs, pd.DataFrame([log_entry])])
except:
    logs = pd.DataFrame([log_entry])

logs.to_csv(LOG_FILE, index=False)

# ---------- EMAIL ----------

body = f"""
Submission Summary

Date: {log_entry['date']}
Time: {log_entry['time']}
Total CSV Rows: {rows_total}
Submitted Rows: {submitted}
"""

msg = MIMEText(body)
msg["Subject"] = "Daily Webform Automation Report"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(EMAIL_FROM, EMAIL_PASS)
server.send_message(msg)
server.quit()
