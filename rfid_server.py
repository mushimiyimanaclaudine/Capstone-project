


from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

import pyscrypt
import base64
import os
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
import smtplib
from email.mime.text import MIMEText

# Secret key for token generation
s = URLSafeTimedSerializer('hzxkdiivohfdizka')  # Use the same secret key as Flask app



from datetime import datetime
import threading
import bcrypt
import webbrowser
from email_alert import send_alert_email
from email_alert import send_password_reset_email
from functools import wraps
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Access denied. Admins only.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


DB_PATH = 'laptop_security.db'
# DB_PATH = r"D:\notes\capstone\practical\laptop_security.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                email TEXT UNIQUE,
                phone_number TEXT,
                department TEXT
            )
        ''')
        conn.commit()

        # You can initialize other tables here if needed


app = Flask(__name__)
app.secret_key = 'hzxkdiivohfdizka'
def send_reset_email(to_email, reset_link):
    sender_email = 'mushimiyimana1998@gmail.com'
    sender_password = 'jxyt oiiq qrmz rvhu'  # NOT your regular password
    subject = 'Password Reset Request'
    body = f'''
    Hello,

    You requested a password reset. Click the link below to reset your password:

    {reset_link}

    This link will expire in 30 minutes.

    If you did not request this, please ignore this email.
    '''

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error sending email: {e}")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)  # Set timeout to avoid locking issues
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL;')  # Enable WAL mode for concurrency
    return conn

from movement_logs import log_event

@app.route('/rfid_scan', methods=['POST'])
def rfid_scan():
    rfid_tag = request.form.get('rfid_tag')

    if not rfid_tag:
        return jsonify({"error": "Missing RFID tag"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.full_name
        FROM users u
        JOIN machines m ON u.id = m.user_id
        JOIN rfid_tags r ON r.id = m.rfid_tag_id
        WHERE r.tag_value = ?
    ''', (rfid_tag,))
    result = cursor.fetchone()

    conn.close()

    if result:
        user_name = result[0]
        log_event(rfid_tag, "Laptop moved without permission", user=user_name)
        send_alert_email(rfid_tag, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if request.headers.get('User-Agent', '').lower().startswith('esp'):
            return jsonify({"status": "unauthorized", "message": "Laptop moved without permission"})
        else:
            flash("Laptop moved without permission! Alert sent.", "unauthorized")
            return redirect(url_for('dashboard'))

    else:
        # Unknown tag detected — do NOT save event to DB
        if request.headers.get('User-Agent', '').lower().startswith('esp'):
            return jsonify({"status": "unknown", "message": f"Unknown RFID tag: {rfid_tag}"})
        else:
            flash(f"Unknown RFID tag detected: {rfid_tag}", "unknown")
            return redirect(url_for('dashboard'))

@app.route('/check_alerts')
def check_alerts():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch the latest unprocessed alert
        cursor.execute("""
            SELECT id, event
            FROM movement_logs
            WHERE event = 'Laptop moved without permission' AND processed = 0
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()

        if row:
            alert_id = row[0]

            # Mark this alert as processed to prevent replay
            cursor.execute("UPDATE movement_logs SET processed = 1 WHERE id = ?", (alert_id,))
            conn.commit()

            conn.close()

            return jsonify({
                "alert": True,
                "alert_id": alert_id,
                "message": row[1]
            })
        else:
            conn.close()
            return jsonify({"alert": False})

    except Exception as e:
        print(f"Error in /check_alerts: {e}")
        return jsonify({"alert": False, "error": str(e)}), 500



#Alter table

conn = sqlite3.connect('laptop_security.db')
cursor = conn.cursor()

# cursor.execute("ALTER TABLE users ADD COLUMN email TEXT;")
# cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT;")
# cursor.execute("ALTER TABLE users ADD COLUMN department TEXT;")



conn.commit()
conn.close()

print("Columns added successfully!")

#===========================



def is_admin():
    if 'username' not in session:
        return False
    username = session['username']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admin WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        department = request.form.get('department')
        role = request.form.get('role')
        password = request.form.get('password')

        if not all([username, phone_number, email, department, role, password]):
            flash("All fields are required", "danger")
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin (username, phone_number, email, department, role, password_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, phone_number, email, department, role, password_hash))
            conn.commit()
            conn.close()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username already exists", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/view_staff_users')
@admin_required
def view_staff_users():
    conn = sqlite3.connect('laptop_security.db')
    c = conn.cursor()
    c.execute("SELECT id, username, phone_number, email, department, role FROM admin WHERE role != 'student'")
    users = c.fetchall()
    conn.close()
    return render_template('view_staff_users.html', users=users)


# @app.route('/edit_staff_role/<int:user_id>', methods=['GET', 'POST'])
# @admin_required
# def edit_update_staff_role(user_id):
#     conn = sqlite3.connect('laptop_security.db')
#     c = conn.cursor()

#     if request.method == 'POST':
#         new_role = request.form['role']
#         c.execute("UPDATE admin SET role = ? WHERE id = ?", (new_role, user_id))
#         conn.commit()
#         conn.close()
#         flash('Role updated successfully.', 'success')
#         return redirect(url_for('view_staff_users'))
#     else:
#         c.execute("SELECT id, username, phone_number, email, department, role FROM admin WHERE id = ?", (user_id,))
#         user = c.fetchone()
#         conn.close()

#         if user:
#             return render_template('edit_staff_user_role.html', user=user)
#         else:
#             flash("User not found.", "danger")
#             return redirect(url_for('view_staff_users'))


@app.route('/update_role', methods=['POST'])
@admin_required
def update_role():
    user_id = request.form['user_id']
    new_role = request.form['new_role']

    conn = sqlite3.connect('laptop_security.db')
    c = conn.cursor()
    c.execute("UPDATE admin SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('view_staff_users'))

@app.route('/edit_staff_user/<int:user_id>', methods=['GET', 'POST'])
def edit_staff_user(user_id):
    conn = sqlite3.connect('laptop_security.db')
    conn.row_factory = sqlite3.Row  # makes rows like dicts
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        phone_number = request.form['phone_number']  # use this variable name consistently
        email = request.form['email']
        department = request.form['department']
        role = request.form['role']

        cursor.execute("""
            UPDATE admin 
            SET username = ?, phone_number = ?, email = ?, department = ?, role = ? 
            WHERE id = ?
        """, (username, phone_number, email, department, role, user_id))

        conn.commit()
        conn.close()
        flash('Staff user updated successfully.', 'success')
        return redirect(url_for('view_staff_users'))

    # GET method - retrieve user data for editing
    cursor.execute("SELECT * FROM admin WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return render_template('edit_staff_user.html', user=user)
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('view_staff_users'))


@app.route('/delete_staff_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_staff_user(user_id):
    conn = sqlite3.connect('laptop_security.db')
    c = conn.cursor()
    c.execute("DELETE FROM admin WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deleted successfully.", "success")
    return redirect(url_for('view_staff_users'))  # or the appropriate view name


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Username and password are required", "danger")
            return redirect(url_for('login'))

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, email, role FROM admin WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            session['username'] = username
            session['email'] = row[1]        # save email
            session['role'] = row[2]         # save role
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()

        if not username_or_email:
            flash('Please enter a username or email.', 'danger')
            return render_template('forgot_password.html')

        conn = sqlite3.connect('laptop_security.db')
        c = conn.cursor()
        c.execute("SELECT id, email FROM admin WHERE username = ? OR email = ?", 
                  (username_or_email, username_or_email))
        user = c.fetchone()
        conn.close()

        if user:
            user_id, email = user
            token = s.dumps(email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)

            # Send email (configure this function for your SMTP)
            send_reset_email(email, reset_url)

            flash('If the username/email exists, a password reset link has been sent to your email.', 'success')
        else:
            flash('No user found with that username or email.', 'danger')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=1800)  # 30 min expiry
    except:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            hashed = generate_password_hash(new_password)
            conn = sqlite3.connect('laptop_security.db')
            c = conn.cursor()
            c.execute("UPDATE admin SET password_hash = ? WHERE email = ?", (hashed, email))
            conn.commit()
            conn.close()
            flash('Password has been reset successfully.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html')

@app.route('/change_admin_password', methods=['GET', 'POST'])
def change_admin_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password'].encode('utf-8')
        new_password = request.form['new_password'].encode('utf-8')
        confirm_password = request.form['confirm_password'].encode('utf-8')

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM admin WHERE username = ?", (session['username'],))
        result = cursor.fetchone()

        if result:
            stored_hash = result[0]
            if check_password_hash(stored_hash, current_password.decode('utf-8')):
                if new_password == confirm_password:
                    new_hash = generate_password_hash(new_password.decode('utf-8'))
                    cursor.execute("UPDATE admin SET password_hash = ? WHERE username = ?", (new_hash, session['username']))
                    conn.commit()
                    flash('Password changed successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('New passwords do not match.', 'error')
            else:
                flash('Current password is incorrect.', 'error')
        else:
            flash('User not found.', 'error')

        conn.close()

    return render_template('change_admin_password.html')

# --- DASHBOARD PAGE ---
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])



@app.route('/register_machine', methods=['GET', 'POST'])
def register_machine():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    users = conn.execute('SELECT id, reg_number, full_name FROM users').fetchall()

    available_tags = conn.execute('''
        SELECT id, tag_value, description FROM rfid_tags
        WHERE id NOT IN (SELECT rfid_tag_id FROM machines WHERE rfid_tag_id IS NOT NULL)
    ''').fetchall()

    if request.method == 'POST':
        machine_id = request.form['machine_id']
        description = request.form['description']
        user_id = request.form['user_id']
        rfid_tag_id = request.form['rfid_tag_id']

        conn.execute(
            'INSERT INTO machines (machine_id, description, user_id, rfid_tag_id) VALUES (?, ?, ?, ?)',
            (machine_id, description, user_id, rfid_tag_id)
        )
        conn.commit()
        conn.close()
        flash('Machine registered successfully!')
        return redirect(url_for('view_machines'))

    conn.close()
    return render_template('register_machine.html', users=users, available_tags=available_tags)
@app.route('/add_rfid_tag', methods=['GET', 'POST'])
def add_rfid_tag():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        tag_value = request.form['tag_value']
        description = request.form['description']
        status = request.form['status']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO rfid_tags (tag_value, description, status) VALUES (?, ?, ?)',
            (tag_value, description, status)
        )
        conn.commit()
        conn.close()

        flash('RFID tag added successfully!')
        return redirect(url_for('view_rfid_tags'))

    return render_template('rfid_tag.html')

@app.route('/view_machines')
def view_machines():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            m.id,
            m.machine_id,
            m.description,
            u.full_name AS user_name,
            u.reg_number AS reg_number,
            r.tag_value
        FROM machines m
        LEFT JOIN users u ON m.user_id = u.id
        LEFT JOIN rfid_tags r ON m.rfid_tag_id = r.id
    ''')

    machines = cursor.fetchall()
    conn.close()

    return render_template('view_machines.html', machines=machines)




@app.route('/view_rfid_tags')
def view_rfid_tags():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('laptop_security.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, tag_value, description FROM rfid_tags ORDER BY id ASC')
    tags = cursor.fetchall()
    conn.close()

    return render_template('view_rfid_tags.html', tags=tags)


@app.route('/edit_rfid_tag/<int:tag_id>', methods=['GET', 'POST'])
def edit_rfid_tag(tag_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        new_value = request.form['tag_value']
        new_description = request.form['description']
        cursor.execute("UPDATE rfid_tags SET tag_value = ?, description = ? WHERE id = ?", (new_value, new_description, tag_id))
        conn.commit()
        conn.close()
        flash('RFID tag updated successfully.')
        return redirect(url_for('view_rfid_tags'))

    cursor.execute("SELECT id, tag_value, description FROM rfid_tags WHERE id = ?", (tag_id,))
    tag = cursor.fetchone()
    conn.close()

    return render_template('edit_rfid_tag.html', tag=tag)

@app.route('/delete_rfid_tag/<int:tag_id>', methods=['POST'])
def delete_rfid_tag(tag_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rfid_tags WHERE id = ?", (tag_id,))
    conn.commit()
    conn.close()

    flash('RFID tag deleted successfully.')
    return redirect(url_for('view_rfid_tags'))

@app.route('/edit_machine/<int:id>', methods=['GET', 'POST'])
def edit_machine(id):
    conn = get_db_connection()
    machine = conn.execute('SELECT * FROM machines WHERE id = ?', (id,)).fetchone()
    if not machine:
        flash('Machine not found.', 'error')
        return redirect(url_for('view_machines'))

    users = conn.execute('SELECT id, full_name FROM users').fetchall()

    # Get all RFID tags not assigned to other machines or include current machine's tag
    available_tags = conn.execute('''
        SELECT * FROM rfid_tags 
        WHERE id NOT IN (SELECT rfid_tag_id FROM machines WHERE id != ?)
    ''', (id,)).fetchall()

    if request.method == 'POST':
        new_machine_id = request.form['machine_id'].strip()
        new_description = request.form['description'].strip()
        new_user_id = int(request.form['user_id'])
        new_rfid_tag_id = int(request.form['rfid_tag_id'])

        # Check duplicates

        # Check machine_id uniqueness (except current machine)
        existing_machine_id = conn.execute(
            'SELECT * FROM machines WHERE machine_id = ? AND id != ?', (new_machine_id, id)
        ).fetchone()
        if existing_machine_id:
            flash('Machine ID already exists.', 'error')
            return redirect(url_for('edit_machine', id=id))

        # Check user uniqueness (except current machine)
        existing_user = conn.execute(
            'SELECT * FROM machines WHERE user_id = ? AND id != ?', (new_user_id, id)
        ).fetchone()
        if existing_user:
            flash('This user is already assigned to another machine.', 'error')
            return redirect(url_for('edit_machine', id=id))

        # Check RFID tag uniqueness (except current machine)
        existing_tag = conn.execute(
            'SELECT * FROM machines WHERE rfid_tag_id = ? AND id != ?', (new_rfid_tag_id, id)
        ).fetchone()
        if existing_tag:
            flash('This RFID tag is already assigned to another machine.', 'error')
            return redirect(url_for('edit_machine', id=id))

        # If all checks pass, update the machine
        conn.execute('''
            UPDATE machines
            SET machine_id = ?, description = ?, user_id = ?, rfid_tag_id = ?
            WHERE id = ?
        ''', (new_machine_id, new_description, new_user_id, new_rfid_tag_id, id))
        conn.commit()
        flash('Machine updated successfully!', 'success')
        return redirect(url_for('view_machines'))

    conn.close()
    return render_template('edit_machine.html', machine=machine, users=users, available_tags=available_tags)


@app.route('/delete_machine/<int:machine_id>', methods=['POST'])
def delete_machine(machine_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM machines WHERE id = ?', (machine_id,))
    conn.commit()
    conn.close()

    flash('Machine deleted successfully.', 'success')  # Message to display
    return redirect(url_for('view_machines'))


@app.route('/view_users')
def view_users():
    if not is_admin():
        flash("Access denied. Admins only.")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, reg_number, email, phone_number, department FROM users")
    users = cursor.fetchall()
    conn.close()

    return render_template('view_users.html', users=users)



# Reset password route
from flask import request, render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
import smtplib
from email.mime.text import MIMEText
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        full_name = request.form['full_name']
        reg_number = request.form['reg_number']
        email = request.form['email']
        phone_number = request.form['phone_number']
        department = request.form['department']

        phone_pattern = re.compile(r'^\d{10}$')
        if not phone_pattern.match(phone_number):
            flash('Phone number must be exactly 10 digits.', 'error')
            conn.close()
            return redirect(url_for('edit_user', user_id=user_id))

        # Check reg_number uniqueness excluding current user
        cursor.execute("SELECT id FROM users WHERE reg_number = ? AND id != ?", (reg_number, user_id))
        if cursor.fetchone():
            flash('Registration number already exists. Please use a unique registration number.', 'error')
            conn.close()
            return redirect(url_for('edit_user', user_id=user_id))

        # Check phone_number uniqueness excluding current user
        cursor.execute("SELECT id FROM users WHERE phone_number = ? AND id != ?", (phone_number, user_id))
        if cursor.fetchone():
            flash('Phone number already exists. Please use a unique phone number.', 'error')
            conn.close()
            return redirect(url_for('edit_user', user_id=user_id))

        try:
            cursor.execute('''
                UPDATE users
                SET full_name = ?, reg_number = ?, email = ?, phone_number = ?, department = ?
                WHERE id = ?
            ''', (full_name, reg_number, email, phone_number, department, user_id))
            conn.commit()
            flash('Student updated successfully', 'success')
        except Exception as e:
            flash(f'Error updating student: {e}', 'error')
        finally:
            conn.close()
        return redirect(url_for('view_users'))

    conn.close()
    return render_template('edit_user.html', user=user)




# Delete user route
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('User deleted successfully.')
    return redirect(url_for('view_users'))


# --- ADD NEW USER ---
from flask import flash, session, redirect, url_for, render_template, request
import sqlite3
import re
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        reg_number = request.form.get('reg_number', '').strip()
        email = request.form.get('email', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        department = request.form.get('department', '').strip()

        # Validate required fields
        if not full_name or not reg_number or not phone_number:
            flash('Full name, Registration number, and Phone number are required.', 'danger')
            return render_template('add_user.html', full_name=full_name, reg_number=reg_number,
                                   email=email, phone_number=phone_number, department=department)

        # Validate registration number format: 2 digits + RP + 5 digits
        if not re.match(r'^\d{2}RP\d{5}$', reg_number):
            flash('Registration number must be 9 characters: 2 digits + "RP" + 5 digits (e.g., 23RP00498).', 'danger')
            return render_template('add_user.html', full_name=full_name, reg_number=reg_number,
                                   email=email, phone_number=phone_number, department=department)

        # Validate phone number format: exactly 10 digits
        if not re.match(r'^\d{10}$', phone_number):
            flash('Phone number must be exactly 10 digits.', 'danger')
            return render_template('add_user.html', full_name=full_name, reg_number=reg_number,
                                   email=email, phone_number=phone_number, department=department)

        # Optional: you can add email validation here if needed

        # Check uniqueness in DB
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE reg_number = ?", (reg_number,))
        if cursor.fetchone():
            flash('Registration number already exists. Please use a unique registration number.', 'danger')
            conn.close()
            return render_template('add_user.html', full_name=full_name, reg_number=reg_number,
                                   email=email, phone_number=phone_number, department=department)

        cursor.execute("SELECT id FROM users WHERE phone_number = ?", (phone_number,))
        if cursor.fetchone():
            flash('Phone number already exists. Please use a unique phone number.', 'danger')
            conn.close()
            return render_template('add_user.html', full_name=full_name, reg_number=reg_number,
                                   email=email, phone_number=phone_number, department=department)

        try:
            cursor.execute('''
                INSERT INTO users (full_name, reg_number, email, phone_number, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (full_name, reg_number, email, phone_number, department))
            conn.commit()
            flash('Student added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding student: {e}', 'danger')
        finally:
            conn.close()

        return redirect(url_for('view_users'))

    # GET request
    return render_template('add_user.html')


# --- MAIN PAGE (SHOW RFID EVENTS) ---
# @app.route('/')
# def index():
#     if 'username' not in session:
#         return redirect(url_for('login'))
#     return render_template('index.html')

#@app.route('/')
#def home():
    # Redirect to login page instead of dashboard
   # return redirect(url_for('login'))

# # --- API TO GET RFID EVENTS ---
# @app.route('/events')
# def get_events():
#     if 'username' not in session:
#         return jsonify({"error": "Unauthorized"}), 401
    
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute("SELECT timestamp, rfid_tag, event FROM events ORDER BY timestamp DESC LIMIT 10")
#     events = cursor.fetchall()
#     conn.close()

#     return jsonify([
#         {"timestamp": t, "rfid_tag": tag, "event": e}
#         for t, tag, e in events
#     ])
@app.route('/view_events', methods=['GET', 'POST'])
def view_events():
    if 'username' not in session:
        return redirect(url_for('login'))

    selected_date = None
    if request.method == 'POST':
        selected_date = request.form.get('selected_date')
    else:
        selected_date = None  # or maybe default to today if you want

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if selected_date:
        # Fetch events for the selected date only
        cursor.execute('''
            SELECT m.id, m.timestamp, m.rfid_tag, m.event, u.reg_number, u.full_name AS user_name
            FROM movement_logs m
            LEFT JOIN users u ON m.user = u.full_name
            WHERE DATE(m.timestamp) = ?
            ORDER BY m.timestamp DESC
            LIMIT 50
        ''', (selected_date,))
    else:
        # Fetch all recent events
        cursor.execute('''
            SELECT m.id, m.timestamp, m.rfid_tag, m.event, u.reg_number, u.full_name AS user_name
            FROM movement_logs m
            LEFT JOIN users u ON m.user = u.full_name
            ORDER BY m.timestamp DESC
            LIMIT 50
        ''')

    events = cursor.fetchall()
    conn.close()

    return render_template('view_events.html', events=events, selected_date=selected_date)



# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


# --- AUTO OPEN BROWSER ON RUN ---
def open_browser():
    webbrowser.open_new('http:// 10.17.107.53:5000/login')


@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'username' not in session:
        flash("Please login to continue.", "warning")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movement_logs WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

    flash(f"Event ID {event_id} deleted successfully.", "success")
    return redirect(url_for('view_events'))

@app.route('/delete_all_events', methods=['POST'])
def delete_all_events():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM movement_logs")
        conn.commit()
        conn.close()
        flash('✅ All events have been deleted successfully.', 'success')
    except Exception as e:
        flash(f'❌ Error deleting all events: {str(e)}', 'error')
    return redirect(url_for('view_events'))
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Example user info from session; adjust keys to your session structure
    user_info = {
        'username': session.get('username'),
        'email': session.get('email', 'Not provided'),
        'role': session.get('role', 'User')
    }
    return render_template('profile.html', user=user_info)   
if __name__ == '__main__':
    threading.Timer(1.0, open_browser).start()
    app.run(host='0.0.0.0', port=5000, debug=True)

