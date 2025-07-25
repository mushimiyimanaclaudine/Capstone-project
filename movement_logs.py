import sqlite3
from datetime import datetime
from email_alert import send_alert_email

DB_PATH = 'laptop_security.db'  # adjust if needed

def log_event(rfid_tag, event, user=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movement_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            rfid_tag TEXT NOT NULL,
            event TEXT NOT NULL,
            user TEXT
        )
    ''')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO movement_logs (timestamp, rfid_tag, event, user)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, rfid_tag, event, user))

    conn.commit()
    conn.close()

    # Send alert for unauthorized access
    if event.lower() == "unauthorized access":
        send_alert_email(rfid_tag, timestamp)
