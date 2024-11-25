from flask import Flask, render_template, request, redirect, url_for, session
from utils.quiz_handler import QuizHandler
import os
import json
import secrets
from datetime import datetime
from models import Subject, engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
app.secret_key = os.urandom(24)

quiz_handler = QuizHandler()


@app.route("/")
def index():
    with sessionmaker(bind=engine)() as db:
        subjects = db.query(Subject).all()
    return render_template("config.html", subjects=subjects)


@app.route("/configure", methods=["POST"])
def configure():
    username = request.form.get("username", "anonymous")
    num_questions = int(request.form.get("num_questions", 50))
    time_limit = int(request.form.get("time_limit", 30))
    shuffle_options = request.form.get("shuffle_options") == "on"
    subject_code = request.form.get("subject", "AIL303m")

    quiz_token = secrets.token_urlsafe(32)
    session["username"] = username
    session["quiz_token"] = quiz_token
    session["subject"] = subject_code

    quiz_handler = QuizHandler(subject_code)  
    quiz = quiz_handler.initialize_quiz(
        username, num_questions, shuffle_options
    )  
    quiz["token"] = quiz_token
    quiz["time_limit"] = time_limit
    quiz["subject"] = {  
        "code": quiz_handler.subject.code,
        "name": quiz_handler.subject.name,
    }
    quiz_handler.save_quiz_state(username, quiz_token, quiz)

    return redirect(url_for("exam"))


@app.route("/exam")
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
