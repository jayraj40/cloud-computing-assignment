from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "users.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT NOT NULL,
            lastname TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            filename TEXT,
            wordcount INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    email = request.form["email"]
    address = request.form["address"]
    uploaded_file = request.files.get("file")

    filename = None
    wordcount = 0

    if uploaded_file and uploaded_file.filename:
        filename = os.path.basename(uploaded_file.filename)
        user_folder = os.path.join(UPLOAD_FOLDER, username)
        os.makedirs(user_folder, exist_ok=True)

        filepath = os.path.join(user_folder, filename)
        uploaded_file.save(filepath)

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            contents = f.read()
            wordcount = len(contents.split())

    conn = get_db()

    try:
        conn.execute("""
            INSERT INTO users
            (username, password, firstname, lastname, email, address, filename, wordcount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, password, firstname, lastname,
            email, address, filename, wordcount
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Username already exists. Please choose another username.", 400

    conn.close()

    return redirect(url_for("profile", username=username))


@app.route("/profile/<username>")
def profile(username):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()

    if user is None:
        return "User not found", 404

    return render_template("profile.html", user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            return redirect(url_for("profile", username=username))

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


@app.route("/download/<username>/<filename>")
def download_file(username, filename):
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    return send_from_directory(
        user_folder,
        filename,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)
