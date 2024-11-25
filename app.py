from flask import Flask, render_template, request, redirect, url_for, session, flash
from utils.quiz_handler import QuizHandler
import os
import json
import secrets
from datetime import datetime
from models import Subject, TestHistory, engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
from sqlalchemy import func

app = Flask(__name__)
app.secret_key = os.urandom(24)

quiz_handler = QuizHandler()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return render_template("login.html", error="Username is required")

        session["username"] = username
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    username = session["username"]
    db = sessionmaker(bind=engine)()
    user = quiz_handler.get_user_progress(username)

    stats = (
        db.query(
            func.count(TestHistory.id).label("tests_taken"),
            (func.avg(TestHistory.score) / 10).label("avg_score"),
            func.sum(TestHistory.time_taken).label("total_time"),
        )
        .filter(TestHistory.user_id == user.id)
        .first()
    )

    active_quiz = None
    if user.active_quiz:
        active_quiz = {
            "subject": user.active_quiz.subject,
            "start_time": datetime.fromisoformat(
                user.active_quiz.quiz_data["start_time"].replace("Z", "+00:00")
            ),
            "quiz_token": user.active_quiz.quiz_token,
        }

    return render_template(
        "dashboard.html", username=username, stats=stats, active_quiz=active_quiz
    )


@app.route("/clear_active_test", methods=["POST"])
@login_required
def clear_active_test():
    username = session["username"]
    quiz_handler.clear_quiz_state(username)
    session.pop("quiz_token", None)
    return redirect(url_for("dashboard"))


@app.route("/history")
@login_required
def history():
    username = session["username"]
    db = sessionmaker(bind=engine)()
    user = quiz_handler.get_user_progress(username)
    tests = (
        db.query(TestHistory)
        .filter_by(user_id=user.id)
        .order_by(TestHistory.completed_at.desc())
        .all()
    )
    return render_template("history.html", tests=tests)


@app.route("/result/<int:test_id>")
@login_required
def view_result(test_id):
    username = session["username"]
    db = sessionmaker(bind=engine)()
    user = quiz_handler.get_user_progress(username)
    test = db.query(TestHistory).filter_by(id=test_id, user_id=user.id).first()

    if not test:
        flash("Test result not found", "error")
        return redirect(url_for("history"))

    try:
        subject_code = test.subject.code if test.subject else "Unknown"
        subject_name = test.subject.name if test.subject else "Unknown Subject"

        results = {
            "score": test.score,
            "correct_count": len(
                [r for r in test.questions.get("results", []) if r.get("is_correct")]
            ),
            "total_questions": len(test.questions.get("results", []))
            if test.questions
            else 0,
            "time_taken": test.time_taken,
            "question_results": test.questions.get("results", []),
            "subject": {"code": subject_code, "name": subject_name},
            "from_history": True,
        }

        return render_template("grade.html", results=results)
    except Exception as e:
        print(f"Error processing test results: {e}")
        flash("Error processing test results", "error")
        return redirect(url_for("history"))


@app.route("/result/<result_token>")
@login_required
def view_result_by_token(result_token):
    username = session["username"]
    results = quiz_handler.get_results(username, result_token)

    if not results:
        flash("Test result not found or expired", "error")
        return redirect(url_for("history"))

    return render_template("grade.html", results=results)


@app.route("/configure", methods=["GET", "POST"])
@login_required
def configure():
    username = session["username"]
    user = quiz_handler.get_user_progress(username)

    if user.active_quiz:
        flash(
            "Please finish or discard your active test before starting a new one.",
            "warning",
        )
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        num_questions = int(request.form.get("num_questions", 50))
        time_limit = int(request.form.get("time_limit", 30))
        shuffle_options = request.form.get("shuffle_options") == "on"
        subject_code = request.form.get("subject", "AIL303m")

        quiz_token = secrets.token_urlsafe(32)
        session["quiz_token"] = quiz_token
        session["subject"] = subject_code

        subject_quiz_handler = QuizHandler(subject_code)
        quiz = subject_quiz_handler.initialize_quiz(
            username, num_questions, shuffle_options
        )
        quiz["token"] = quiz_token
        quiz["time_limit"] = time_limit
        quiz["subject"] = {
            "code": subject_quiz_handler.subject.code,
            "name": subject_quiz_handler.subject.name,
        }
        subject_quiz_handler.save_quiz_state(username, quiz_token, quiz)

        return redirect(url_for("exam"))

    db = sessionmaker(bind=engine)()
    subjects = db.query(Subject).all()
    return render_template("config.html", subjects=subjects)


@app.route("/exam")
@login_required
def exam():
    if "quiz_token" not in session:
        return redirect(url_for("index"))

    username = session.get("username")
    quiz_token = session.get("quiz_token")
    subject_name = session.get("subject", "AIL303m")

    quiz_handler = QuizHandler(subject_name)

    request_token = request.args.get("token")
    if request_token and request_token == quiz_token:
        quiz = quiz_handler.get_quiz_state(username, request_token)
    else:
        quiz = quiz_handler.get_quiz_state(username, quiz_token)

    if not quiz:
        return redirect(url_for("index"))

    if "subject" not in quiz:
        quiz["subject"] = {
            "code": quiz_handler.subject.code,
            "name": quiz_handler.subject.name,
        }

    if "start_time" not in quiz or not quiz["start_time"]:
        quiz["start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        quiz_handler.save_quiz_state(username, quiz_token, quiz)

    time_limit = quiz.get("time_limit", 30)

    return render_template(
        "exam.html",
        quiz=quiz,
        time_limit=time_limit,
        enumerate=enumerate,
        hide_nav=True,
    )


@app.route("/submit", methods=["POST"])
@login_required
def submit():
    if "quiz_token" not in session:
        return redirect(url_for("index"))

    try:
        answers_json = request.form.get("answers", "[]")
        answers = json.loads(answers_json)

        formatted_answers = {
            str(i + 1): answer for i, answer in enumerate(answers) if answer is not None
        }

        username = session.get("username")
        subject_name = session.get("subject", "AIL303m")
        quiz_handler = QuizHandler(subject_name)

        quiz_token = session.get("quiz_token")
        quiz = quiz_handler.get_quiz_state(username, quiz_token)

        if not quiz:
            return redirect(url_for("index"))

        results = quiz_handler.grade_quiz(username, quiz, formatted_answers)

        results["subject"] = {
            "code": quiz_handler.subject.code,
            "name": quiz_handler.subject.name,
        }

        result_token = secrets.token_urlsafe(16)
        quiz_handler.save_results(username, result_token, results)

        session["result_token"] = result_token

        session.pop("quiz_token", None)
        quiz_handler.clear_quiz_state(username)

        return redirect(url_for("grade"))
    except Exception as e:
        print(f"Error during quiz submission: {e}")
        session["error"] = (
            "An error occurred while submitting your quiz. Please try again."
        )
        return redirect(url_for("index"))


@app.route("/grade")
@login_required
def grade():
    result_token = session.get("result_token")
    if not result_token:
        return redirect(url_for("index"))

    username = session.get("username")
    results = quiz_handler.get_results(username, result_token)

    if not results:
        return redirect(url_for("index"))

    session.pop("result_token", None)
    quiz_handler.clear_results(username, result_token)

    return render_template("grade.html", results=results)


@app.route("/debug/user/<username>")
def debug_user(username):
    if not app.debug:
        return "Debug mode is disabled", 403

    user = quiz_handler.get_user_progress(username)
    if not user:
        return "User not found", 404

    debug_info = {
        "username": user.username,
        "penalty_questions": user.penalty_questions,
        "penalty_count": len(user.penalty_questions),
        "question_bag": user.question_bag,
        "question_bag_count": len(user.question_bag),
        "active_quiz": bool(user.active_quiz),
        "quiz_token": user.active_quiz.quiz_token if user.active_quiz else None,
        "test_history": [
            {
                "score": test.score,
                "completed_at": test.completed_at.isoformat(),
                "time_taken": test.time_taken,
            }
            for test in user.tests
        ],
    }
    return debug_info


if __name__ == "__main__":
    app.run(debug=True)
