import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_alert_email(rfid_tag, timestamp):
    sender = 'mushimiyimana1998@gmail.com'
    receiver = 'mushimiyimanaclau2000@gmail.com'
    subject = '🚨 Laptop moved without permission'

    body = f"""
    Security Alert: Laptop moved without permission

    RFID Tag: {rfid_tag}
    Timestamp: {timestamp}
    """

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, 'hzxkdiivohfdizka')  # Your Gmail app password here
        server.send_message(msg)
        server.quit()
        print("✅ Email alert sent.")
    except Exception as e:
        print("❌ Failed to send email:", e)

def send_password_reset_email(to_email, username, reset_link):
    sender = 'mushimiyimana1998@gmail.com'
    subject = '🔑 Password Reset Request'
    body = f"""
Hello {username},

You requested a password reset.

Please click the link below to reset your password:

{reset_link}

If you did not request this, please ignore this email.

Best regards,
Your RFID Security Team
"""

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, 'hzxkdiivohfdizka')  # Your Gmail app password here
        server.send_message(msg)
        server.quit()
        print("✅ Password reset email sent.")
    except Exception as e:
        print("❌ Failed to send password reset email:", e)

if __name__ == "__main__":
    test_rfid = "RFID1234567890"
    test_time = "2025-07-02 10:30:00"
    send_alert_email(test_rfid, test_time)
