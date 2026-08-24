from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "wellness_ultimate_pro_key_2026"


def get_db_connection():
    conn = sqlite3.connect("mental_health.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        password_hash TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS stress_result (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        score INTEGER,
        level TEXT
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        rating INTEGER,
        message TEXT
    )""")
    conn.commit()
    conn.close()


init_db()


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if 'user' not in session or 'student_id' not in session:
            return redirect(url_for('home'))
        return view_func(*args, **kwargs)
    return wrapped


@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template("login.html")


@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name', '').strip()
    password = request.form.get('password', '')

    if not name or not password:
        return render_template("login.html", error="Please enter both name and password.")

    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM students WHERE name = ?", (name,)).fetchone()
    conn.close()

    if existing is None:
        return render_template("login.html", error="No account found with that name. Please register first.")

    if not check_password_hash(existing['password_hash'], password):
        return render_template("login.html", error="Incorrect password. Please try again.")

    session['user'] = name
    session['student_id'] = existing['id']
    return redirect(url_for('dashboard'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')

        if not name or not password:
            return render_template("register.html", error="Please enter both name and password.")

        conn = get_db_connection()
        try:
            password_hash = generate_password_hash(password)
            cursor = conn.execute(
                "INSERT INTO students (name, password_hash) VALUES (?, ?)", (name, password_hash)
            )
            conn.commit()
            student_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="That name is already registered. Please sign in instead.")

        conn.close()
        session['user'] = name
        session['student_id'] = student_id
        return redirect(url_for('dashboard'))

    return render_template("register.html")


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    last_test = conn.execute(
        "SELECT * FROM stress_result WHERE student_id = ? ORDER BY id DESC LIMIT 1", (session['student_id'],)
    ).fetchone()
    count = conn.execute(
        "SELECT COUNT(*) FROM stress_result WHERE student_id = ?", (session['student_id'],)
    ).fetchone()[0]
    conn.close()
    return render_template("dashboard.html", user=session['user'], last_test=last_test, count=count, active_page='dashboard')


@app.route('/quiz')
@login_required
def quiz():
    return render_template("quiz.html", active_page='quiz')


@app.route('/submit_quiz', methods=['POST'])
@login_required
def submit_quiz():
    q_values = [v for k, v in request.form.items() if k.startswith('q')]
    score = sum(int(v) for v in q_values)
    level = "Low Stress" if score <= 10 else "Moderate Stress" if score <= 20 else "High Stress"

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO stress_result (student_id, score, level) VALUES (?, ?, ?)", (session['student_id'], score, level)
    )
    conn.commit()
    conn.close()
    return render_template("result.html", score=score, level=level, active_page='quiz')


@app.route('/tips')
@login_required
def tips():
    return render_template("tips.html", active_page='tips')


@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        rating = request.form.get('rating')
        msg = request.form.get('message')
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO feedback (student_id, rating, message) VALUES (?, ?, ?)", (session['student_id'], rating, msg)
        )
        conn.commit()
        conn.close()
        return render_template("feedback.html", active_page='feedback', submitted=True)
    return render_template("feedback.html", active_page='feedback')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)