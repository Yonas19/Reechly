import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configuration ---
SENDER_EMAIL = "yonjr0936@gmail.com" # Replace with your email
APP_PASSWORD = "gxwchcxrsraxfqxz" # Replace with your app password
TARGET_EMAIL = "yonashaseffa@gmail.com" # Send it to yourself for the test

def send_test_email():
    try:
        # 1. Set up the email structure
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = TARGET_EMAIL
        msg['Subject'] = "Automated Outreach Test"
        
        body = "If you are reading this, the Python email engine is working perfectly."
        msg.attach(MIMEText(body, 'plain'))
        
        # 2. Connect to Gmail's SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Secure the connection
        # 2. Connect to Gmail's SMTP server using port 465 and SMTP_SSL
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        # server.starttls() is not needed with SMTP_SSL
        
        # 3. Login and send
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print("Success! The test email has been sent.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_email()