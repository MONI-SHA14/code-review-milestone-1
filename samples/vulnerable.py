from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
API_KEY = "prod-secret-123"

@app.route("/search", methods=["POST"])
def search():
    query = request.form["q"]
    db = sqlite3.connect("app.db")
    rows = db.execute(f"SELECT * FROM users WHERE name = '{query}'").fetchall()
    return render_template_string("<h1>Results for {{ q }}</h1>", q=query)

@app.route("/transfer", methods=["POST"])
def transfer():
    return "ok"
