hello everyone
# Real-Time IoT-Based Laptop Security and Notification System

This project provides a **real-time RFID-based tracking and alert system** for securing laboratory laptops at RP-Ngoma College. It uses **NodeMCU (ESP8266)** to read RFID tags and send events to a **Flask-based web application**. The system allows administrators and lab assistants to monitor, register, and manage lab laptops and users securely.

## Key Features

**Login system** with two roles: `Admin` and `Lab Assistant`
**RFID event logging** (unauthorized access triggers buzzer & email alert)
**Forgot Password / Reset Password** functionality via email
**Change Password** after login
**View & manage users (staff)** — only accessible to admins
**Register and manage machines** (linked with RFID tag and student info)
**Real-time dashboard** showing all activities done by the users 
**Email alerts** for unauthorized laptop moved from the labs
**Secure password hashing** using scrypt

## Project Structure

```bash
Capstone-project/
│
├── static/                    # CSS, JS, images
├── templates/                 # HTML templates
│   ├── auth.html              # Base layout for login, reset, etc.
│   ├── dashboard.html         # Main dashboard
│   ├── login.html             # Login page
│   ├── register_machine.html  # Register machine form
│   ├── view_logs.html         # Movement logs
│   ├── view_staff_users.html  # Admin-only: view staff
│   ├── change_password.html   # Password change
│   ├── forgot_password.html   # Request reset link
│   └── reset_password.html    # Reset password form
│
├── rfid_server.py             # Main Flask app
├── database/
│   └── laptop_security.db     # SQLite DB
│
├── nodemcu_code/              # ESP8266 Arduino code folder
│   └── rfid_security.ino      # Your Arduino sketch
│
├── .gitignore
├── requirements.txt
└── README.md
