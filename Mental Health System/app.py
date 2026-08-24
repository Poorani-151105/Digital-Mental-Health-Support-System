from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        regno TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stress_result(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regno TEXT,
        score INTEGER,
        level TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/login', methods=['POST'])
def login():

    name = request.form['name']
    regno = request.form['regno']

    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO students (name,regno) VALUES (?,?)",(name,regno))

    conn.commit()
    conn.close()

    return render_template("quiz.html")


@app.route('/result', methods=['POST'])
def result():

    score = 0

    for i in range(1,11):
        score += int(request.form[f'q{i}'])

    if score <= 15:
        level = "Low Stress"
        description = "You are managing stress well. Maintain healthy habits like exercise and good sleep."

    elif score <= 25:
        level = "Moderate Stress"
        description = "You may be experiencing some stress. Try meditation, take breaks while studying and manage time properly."

    else:
        level = "High Stress"
        description = "You are experiencing high stress. Talk with friends, teachers or counselors and practice relaxation techniques."

    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO stress_result (regno,score,level) VALUES (?,?,?)",
        ("student",score,level)
    )

    conn.commit()
    conn.close()

    return render_template("result.html",
                           level=level,
                           description=description)


@app.route('/chart')
def chart():
    return render_template("chart.html")


@app.route('/stress_data')
def stress_data():

    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()

    cursor.execute("SELECT level, COUNT(*) FROM stress_result GROUP BY level")

    data = {"Low Stress":0,"Moderate Stress":0,"High Stress":0}

    for row in cursor.fetchall():
        data[row[0]] = row[1]

    conn.close()

    return jsonify([
        data["Low Stress"],
        data["Moderate Stress"],
        data["High Stress"]
    ])


@app.route('/history')
def history():

    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()

    cursor.execute("SELECT score,level FROM stress_result")

    results = cursor.fetchall()

    conn.close()

    return render_template("history.html", results=results)


@app.route('/feedback')
def feedback():
    return render_template("feedback.html")


@app.route('/save_feedback', methods=['POST'])
def save_feedback():

    message = request.form['feedback']

    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO feedback (message) VALUES (?)",(message,))

    conn.commit()
    conn.close()

    return "Feedback Saved Successfully!"

if __name__ == "__main__":
    app.run(debug=True)