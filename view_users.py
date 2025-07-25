import sqlite3

# Connect to your database
conn = sqlite3.connect('laptop_security.db')
cursor = conn.cursor()

# Select all from admin table
print("Admin Table:")
cursor.execute("SELECT id, username, password_hash FROM admin")
admins = cursor.fetchall()
for admin in admins:
    print(admin)

# Select all from users table
print("\nUsers Table:")
cursor.execute("SELECT id, username, password_hash FROM users")
users = cursor.fetchall()
for user in users:
    print(user)

conn.close()
