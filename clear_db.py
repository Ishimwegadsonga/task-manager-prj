import sqlite3

try:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users")
    conn.commit()

    print("All user data deleted successfully!")

except Exception as e:
    print("Error:", e)

finally:
    conn.close()
