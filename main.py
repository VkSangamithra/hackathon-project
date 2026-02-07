from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey123"


# ---------------- DATABASE SETUP ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        userid TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userid TEXT,
        code TEXT,
        concept TEXT,
        analogy TEXT,
        hint TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("login.html")


# ---------------- USER SIGNUP ----------------

@app.route("/signup", methods=["POST"])
def signup():
    fullname = request.form.get("fullname")
    email = request.form.get("email")
    userid = request.form.get("userid")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (fullname, email, userid, password) VALUES (?, ?, ?, ?)",
            (fullname, email, userid, password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "User ID already exists!"

    conn.close()

    session["user"] = userid
    return redirect("/dashboard")


# ---------------- USER LOGIN ----------------

@app.route("/user_login", methods=["POST"])
def user_login():
    userid = request.form.get("userid")
    password = request.form.get("password")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE userid=? AND password=?",
        (userid, password)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        session.clear()
        session["user"] = userid
        return redirect("/dashboard")
    else:
        return "Invalid User Credentials!"


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin_login", methods=["POST"])
def admin_login():
    adminid = request.form.get("adminid")
    adminpass = request.form.get("adminpass")

    # Hardcoded admin credentials
    if adminid == "admin1" and adminpass == "admin123":
        session.clear()
        session["admin"] = adminid
        return redirect("/admin_dashboard")
    else:
        return "Invalid Admin Credentials!"


# ---------------- USER DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT code, concept, timestamp
        FROM analysis_history
        WHERE userid=?
        ORDER BY id DESC
        LIMIT 5
    """, (session["user"],))

    history = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html",
                           user=session["user"],
                           history=history)


# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT fullname, email, userid FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("admin.html",
                           admin=session["admin"],
                           users=users)


# ---------------- AI ANALYZER ----------------

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user" not in session:
        return jsonify({"concept": "Login required", "analogy": "", "hint": ""})

    code = request.form.get("code")

    concept = ""
    analogy = ""
    hint = ""

    if "def" in code and ":" not in code:
        concept = "Function definition syntax issue detected."
        analogy = "Like writing a sentence without punctuation."
        hint = "What symbol must follow a function declaration?"

    elif "while" in code and "break" not in code:
        concept = "Possible infinite loop."
        analogy = "Like a treadmill that never stops."
        hint = "What ensures your loop exits?"

    elif "if" in code and ":" not in code:
        concept = "Missing colon in conditional statement."
        analogy = "Like opening a door without hinges."
        hint = "What does Python expect after an if condition?"

    else:
        concept = "Structure looks logically acceptable."
        analogy = "Like a building that looks stable from outside."
        hint = "Check indentation and edge cases."

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analysis_history (userid, code, concept, analogy, hint)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session["user"],
        code,
        concept,
        analogy,
        hint
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "concept": concept,
        "analogy": analogy,
        "hint": hint
    })


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
