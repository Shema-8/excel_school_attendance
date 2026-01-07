from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

# -----------------------------
# APP CONFIGURATION
# -----------------------------
app = Flask(__name__)
app.secret_key = "excel_school_secret_key"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db():
    return sqlite3.connect("database.db")


# -----------------------------
# LOGIN ROUTE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[4]

            if user[4] == "teacher":
                return redirect("/teacher")
            elif user[4] == "headmaster":
                return redirect("/headmaster")

    return render_template("login.html")


# -----------------------------
# TEACHER DASHBOARD
# -----------------------------
@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher":
        return redirect("/")
    return render_template("teacher_dashboard.html")


# -----------------------------
# MARK ATTENDANCE
# -----------------------------
@app.route("/attendance", methods=["GET", "POST"])
def mark_attendance():
    if session.get("role") != "teacher":
        return redirect("/")

    teacher_id = session["user_id"]
    today = datetime.now().strftime("%Y-%m-%d")
    db = get_db()

    class_info = db.execute(
        "SELECT * FROM classes WHERE teacher_id=?",
        (teacher_id,)
    ).fetchone()

    students = db.execute(
        "SELECT * FROM students WHERE class_id=?",
        (class_info[0],)
    ).fetchall()

    if request.method == "POST":
        absent_students = []

        for student in students:
            status = request.form.get(f"status_{student[0]}")

            db.execute(
                "INSERT INTO attendance VALUES (NULL,?,?,?,?,?,?)",
                (
                    student[0],
                    class_info[0],
                    today,
                    status,
                    teacher_id,
                    datetime.now()
                )
            )

            if status == "Absent":
                absent_students.append(student[0])

        for sid in absent_students:
            db.execute(
                "INSERT INTO absent_records VALUES (NULL,?,?,?,?)",
                (today, class_info[0], sid, teacher_id)
            )

        db.commit()
        return redirect("/teacher")

    return render_template("mark_attendance.html", students=students)


# -----------------------------
# HEADMASTER DASHBOARD
# -----------------------------
@app.route("/headmaster")
def headmaster_dashboard():
    if session.get("role") != "headmaster":
        return redirect("/")

    today = datetime.now().strftime("%Y-%m-%d")
    db = get_db()

    summary = db.execute("""
        SELECT status, COUNT(*)
        FROM attendance
        WHERE date=?
        GROUP BY status
    """, (today,)).fetchall()

    absentees = db.execute("""
        SELECT students.full_name, classes.class_name
        FROM absent_records
        JOIN students ON students.id = absent_records.student_id
        JOIN classes ON classes.id = absent_records.class_id
        WHERE absent_records.date=?
    """, (today,)).fetchall()

    return render_template(
        "headmaster_dashboard.html",
        summary=summary,
        absentees=absentees
    )


# -----------------------------
# CONFIRM SMS PAGE
# -----------------------------
@app.route("/confirm_sms")
def confirm_sms():
    if session.get("role") != "headmaster":
        return redirect("/")
    return render_template("confirm_sms.html")


# -----------------------------
# SEND SMS (SIMULATED)
# -----------------------------
@app.route("/send_sms", methods=["POST"])
def send_sms():
    if session.get("role") != "headmaster":
        return redirect("/")

    today = datetime.now().strftime("%Y-%m-%d")
    db = get_db()

    absentees = db.execute("""
        SELECT students.full_name, students.parent_phone
        FROM absent_records
        JOIN students ON students.id = absent_records.student_id
        WHERE absent_records.date=?
    """, (today,)).fetchall()

    for full_name, phone in absentees:
        message = f"""
Dear parents, we would like to ask and know why 
{full_name} is absent today. Thank you.

Babyeyi dufatanyije kurera, twasabaga kumenya ngo mutumenyeshe impamvu
{full_name} yasibye ishuri uyu munsi. Murakoze.
"""
        # SMS simulation (replace with real SMS API later)
        print("------------------------------------------------")
        print("SMS SENT TO:", phone)
        print(message)
        print("------------------------------------------------")

    return redirect("/headmaster")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# -----------------------------
# RUN APPLICATION
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
