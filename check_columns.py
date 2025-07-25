import sqlite3

conn = sqlite3.connect("laptop_security.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(movement_logs)")
for column in cursor.fetchall():
    print(column)

conn.close()
