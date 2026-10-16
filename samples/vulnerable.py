import sqlite3

def find_user(user_id):
    connection = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE id = " + user_id
    return connection.execute(query).fetchall(
