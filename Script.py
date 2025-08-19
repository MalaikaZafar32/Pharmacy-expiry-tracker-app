import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

SAVE_FOLDER = "saved_data"

# Loop over all user files
for filename in os.listdir(SAVE_FOLDER):
    if filename.endswith(".xlsx"):
        user_email = filename.replace(".xlsx", "")
        filepath = os.path.join(SAVE_FOLDER, filename)

        df = pd.read_excel(filepath)
        today = pd.to_datetime("today").normalize()
        expired = df[df['Expiry Date'] < today]

        if expired.empty:
            print(f"✅ No expired medicines for {user_email}")
            continue

        subject = "⚠️ Weekly Pharmacy Expiry Alert"
        body = f"Hello {user_email},\n\nThe following medicines are expired:\n\n{expired.to_string(index=False)}"

        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = user_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, user_email, msg.as_string())

        print(f"📩 Alert sent to {user_email}")
