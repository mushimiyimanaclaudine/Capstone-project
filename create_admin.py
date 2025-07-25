import sqlite3
import bcrypt

conn = sqlite3.connect('laptop_security.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
)
''')


username = 'admin'
password = 'admin123'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

try:
    cursor.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', (username, hashed.decode('utf-8')))
    print("Admin user created.")
except sqlite3.IntegrityError:
    print("Admin already exists.")

conn.commit()
conn.close()
