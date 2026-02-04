import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
import os

# ------------------ CONFIG ------------------

CSV_FILE = "data.csv"
LOG_FILE = "logs.csv"

FORM_URL = "https://forms.office.com/Pages/ResponsePage.aspx?id=1Xu4eN-wo06NVeqxu5DEPF248rZ7rzVPhTL29kjDFtlUODRCMkpFSzY0OTJWNlZBTEIwVTlMQzlPRy4u&origin=QRCode"  # <-- replace with your real form URL

EMAIL_FROM = "stahleesh@gmail.com"      # sender Gmail
EMAIL_TO = "sewarnet2050@gmail.com"        # receiver Gmail (can be same)
EMAIL_PASS = os.environ.get("EMAIL_PASS")  # GitHub secret

# ------------------ LOAD DATA ------------------

df = pd.read_csv(CSV_FILE)
rows_total = len(df)

# Shuffle all rows (submit all 37 randomly)
selected = df.sample(frac=1).reset_index(drop=True)

submitted = 0

# ------------------ FORM SUBMISSION ------------------

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    for _, row in selected.iterrows():
        page.goto(FORM_URL)

        # Fill form fields (adjust selectors as needed)
        page.fill("input[name='name']", row["name"])
        page.fill("input[name='email']", row["email"])
        page.fill("input[name='phone']", str(row["phone"]))
        page.fill("input[name='city']", row["city"])

        # Click submit button
        page.click("button[type='submit']")

        # Wait 2 seconds for submission to complete
        page.wait_for_timeout(2000)

        submitted += 1

    browser.close()

# ------------------ LOGGING ------------------

now = datetime.now()

log_entry = {
    "date": now.strftime("%Y-%m-%d"),
    "time": now.strftime("%H:%M"),
    "total_rows": rows_total,
    "submitted_rows": submitted
}

try:
    logs = pd.read_csv(LOG_FILE)
    logs = pd.concat([logs, pd.DataFrame([log_entry])], ignore_index=True)
except FileNotFoundError:
    logs = pd.DataFrame([log_entry])

logs.to_csv(LOG_FILE, index=False)

# ------------------ EMAIL SUMMARY ------------------

body = f"""
Daily Webform Submission Summary

Date: {log_entry['date']}
Time: {log_entry['time']}
Total CSV Rows: {rows_total}
Submitted Rows: {submitted}
"""

msg = MIMEText(body)
msg["Subject"] = "Daily Webform Automation Report"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

# Send email via Gmail
server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(EMAIL_FROM, EMAIL_PASS)
server.send_message(msg)
server.quit()
