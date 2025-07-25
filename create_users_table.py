import sqlite3
import bcrypt

# Connect to your SQLite database
conn = sqlite3.connect('laptop_security.db')
cursor = conn.cursor()

# Create users table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# Optional: Create a default admin user
username = 'admin'
password = 'admin123'

# Hash the password
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

try:
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    print(f"Default admin user '{username}' created.")
except sqlite3.IntegrityError:
    print(f"User '{username}' already exists.")

conn.commit()
conn.close()
