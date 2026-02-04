import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
import os
import json
import time

# ---------------- CONFIG ----------------

CSV_FILE = "data.csv"
LOG_FILE = "logs.csv"
JS_FILE = "saad_autofill.js"  # Your extension JS file

FORM_URL = "https://your-form-url.com"  # <-- replace with real form URL

EMAIL_FROM = "youremail@gmail.com"
EMAIL_TO = "destination@gmail.com"
EMAIL_PASS = os.environ.get("EMAIL_PASS")  # GitHub secret

# ---------------- LOAD CSV ----------------

df = pd.read_csv(CSV_FILE)
rows_total = len(df)

# Shuffle all rows randomly
selected = df.sample(frac=1).reset_index(drop=True)

# Convert rows to list of lists (for JS)
csv_rows_as_list = selected.values.tolist()

# ------------------ AUTOMATION ------------------

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto(FORM_URL)

    # Inject your JS content script
    page.add_script_tag(path=JS_FILE)

    # Pass CSV data to JS and start automation
    page.evaluate("""
        (data) => {
            window.currentCSVData = data.rows;
            window.currentRowIndex = 0;
            window.isRunning = true;
            // Call your existing processRow function
            if (typeof processRow === "function") {
                processRow(window.currentCSVData[0]);
            }
        }
    """, {"rows": csv_rows_as_list})

    # Wait until all rows are processed
    # We poll for JS variable `isRunning` to become False
    while True:
        is_running = page.evaluate("window.isRunning")
        if not is_running:
            break
        time.sleep(2)

    browser.close()

# ------------------ LOGGING ------------------

now = datetime.now()
log_entry = {
    "date": now.strftime("%Y-%m-%d"),
    "time": now.strftime("%H:%M"),
    "total_rows": rows_total,
    "submitted_rows": rows_total
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
Submitted Rows: {rows_total}
"""

msg = MIMEText(body)
msg["Subject"] = "Daily Webform Automation Report"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server.login(EMAIL_FROM, EMAIL_PASS)
server.send_message(msg)
server.quit()
