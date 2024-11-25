import pandas as pd
import random
import ast
import csv
import os
from sqlalchemy.orm import sessionmaker
from models import engine, User, TestHistory, ActiveQuiz, QuizResult, Subject
from datetime import datetime, timedelta
import re
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizHandler:
    def __init__(self, subject_code: str = "AIL303m"):
        # Get subject from database
        self.db = sessionmaker(bind=engine)()
        self.subject = self.db.query(Subject).filter_by(code=subject_code).first()
        if not self.subject:
            raise ValueError(f"Subject {subject_code} not found")
            
        self.quiz_file = os.path.join("data", self.subject.data_file)
        try:
            self.questions = self._load_questions()
        except Exception as e:
            logger.error(f"Failed to load questions for {subject_code}: {e}")
            self.questions = []

    def _is_image_path(self, text):
        return isinstance(text, str) and (
            text.startswith("static/img/")
            and any(ext in text.lower() for ext in [".png", ".jpg", ".jpeg", ".gif"])
        )

    def _parse_options(self, options_str):
        """
        Custom parser for options and correct_answers strings from CSV.
        """
        try:
            options_str = options_str.replace("\\n", "\n")

            options_str = options_str.strip().strip('"').strip("'")

            options = re.findall(r"\[.*?\]|\".*?\"|'.*?'|[^,]+", options_str)

            cleaned_options = []
            for opt in options:
                opt = opt.strip().strip('"').strip("'")
                if opt.startswith("[") and opt.endswith("]"):
                    opt = opt[1:-1].strip()
                cleaned_options.append(opt)
            return cleaned_options
        except Exception as e:
            print(f"Error parsing options: {options_str}, error: {e}")
            return []

    def _clean_list_string(self, s):
        """Helper method to clean and parse list strings from CSV"""
        try:
            if not s or not isinstance(s, str):
                return []

            s = s.strip()

            if not s.startswith("["):
                return [s.replace("\\n", "\n").strip()]

            try:
                s = s.replace("\\n", "\n")
                s = s.replace("\r", "")
                s = s.replace("'''", "'").replace('"""', '"')

                return ast.literal_eval(s)
            except (ValueError, SyntaxError):
                items = []
                current_item = ""
                in_string = False
                escape = False
                brackets = 0

                for char in s[1:-1]:
                    if escape:
                        current_item += char
                        escape = False
                        continue

                    if char == "\\":
                        escape = True
                        current_item += char
                        continue

                    if char in "\"'":
                        in_string = not in_string
                        current_item += char
                        continue

                    if not in_string:
                        if char == "[":
                            brackets += 1
                        elif char == "]":
                            brackets -= 1
                        elif char == "," and brackets == 0:
                            items.append(current_item.strip().strip("'\""))
                            current_item = ""
                            continue

                    current_item += char

                if current_item:
                    items.append(current_item.strip().strip("'\""))

                return [item for item in items if item]

        except Exception as e:
            print(f"Error cleaning list string: {s}, error: {e}")

            return [s.replace("\\n", "\n").strip()]

    def _load_questions(self) -> List[Dict[str, Any]]:
        import sys

        maxInt = sys.maxsize
        while True:
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt / 10)

        try:
            df = pd.read_csv(
                self.quiz_file,
                names=['question', 'choices', 'answer'],  # Define column names explicitly
                skiprows=1,  # Skip the header row
                quoting=csv.QUOTE_ALL,
                escapechar="\\",
                encoding="utf-8",
                engine="python",
                on_bad_lines="skip",
            )

            questions = []

            for index, row in df.iterrows():
                try:
                    if len(row) < 3:
                        print(f"Skipping row {index}: Insufficient columns")
                        continue

                    text = str(row['question']).strip()
                    options_str = str(row['choices'])  
                    correct_answers_str = str(row['answer'])  # Changed from 'answers' to 'answer' to match CSV
                    
                    # Add debug logging
                    print(f"Reading row {index}:")
                    print(f"Question: {text}")
                    print(f"Options string: {options_str}")
                    print(f"Answers string: {correct_answers_str}")

                    options = self._clean_list_string(options_str)
                    correct_answers = self._clean_list_string(correct_answers_str)

                    if not options or not correct_answers:
                        print(
                            f"Skipping row {index}: No valid options or correct answers"
                        )
                        continue

                    text = text.replace("\\n", "\n")

                    image_url = None
                    if "[Image:" in text:
                        start = text.find("[Image:") + 7
                        end = text.find("]", start)
                        image_url = text[start:end].strip()
                        text = text[: start - 7].strip()

                    formatted_options = []
                    for opt in options:
                        if self._is_image_path(opt):
                            formatted_options.append(
                                {"type": "image", "content": "/" + opt.strip()}
                            )
                        else:
                            formatted_options.append(
                                {"type": "text", "content": opt.strip()}
                            )

                    question = {
                        "text": text,
                        "image_url": "/" + image_url if image_url else None,
                        "options": formatted_options,
                        "correct_answers": correct_answers,
                        "option_count": len(options),
                        "has_image_options": any(
                            self._is_image_path(opt) for opt in options
                        ),
                    }
                    questions.append(question)
                except Exception as e:
                    print(f"Error parsing row at index {index}, skipping: {str(e)}")
                    continue

            return questions
        except Exception as e:
            logger.error(f"Error loading questions from CSV: {e}")
            raise

    def get_user_progress(self, username):
        user = self.db.query(User).filter_by(username=username).first()
        if not user:
            user = User(username=username, question_bag=[], penalty_questions={})
            self.db.add(user)
            self.db.commit()
        return user

    def save_quiz_state(self, username, quiz_token, quiz_data):
        user = self.get_user_progress(username)
        active_quiz = user.active_quiz
        if not active_quiz:
            active_quiz = ActiveQuiz(user=user, subject=self.subject)
        
        active_quiz.quiz_token = quiz_token
        active_quiz.quiz_data = quiz_data
        self.db.add(active_quiz)
        self.db.commit()

    def get_quiz_state(self, username, quiz_token):
        user = self.get_user_progress(username)
        if user.active_quiz and user.active_quiz.quiz_token == quiz_token:
            return user.active_quiz.quiz_data
        return None

    def clear_quiz_state(self, username):
        user = self.get_user_progress(username)
        if user.active_quiz:
            self.db.delete(user.active_quiz)
            self.db.commit()

    def save_results(self, username, result_token, results):
        user = self.get_user_progress(username)
        expires_at = datetime.now() + timedelta(minutes=30)

        quiz_result = QuizResult(
            user_id=user.id,
            subject=self.subject,
            result_token=result_token,
            results=results,
            expires_at=expires_at,
        )

        self.db.add(quiz_result)
        self.db.commit()

    def get_results(self, username, result_token):
        user = self.get_user_progress(username)
        quiz_result = (
            self.db.query(QuizResult)
            .filter_by(user_id=user.id, result_token=result_token)
            .first()
        )

        if quiz_result and quiz_result.expires_at > datetime.now():
            return quiz_result.results
        return None

    def clear_results(self, username, result_token):
        user = self.get_user_progress(username)
        self.db.query(QuizResult).filter_by(
            user_id=user.id, result_token=result_token
        ).delete()
        self.db.commit()

    def initialize_quiz(self, username, num_questions, shuffle_options=False):
        user = self.get_user_progress(username)

        print(f"Initializing quiz with {num_questions} questions")
        print(f"Current penalty questions: {user.penalty_questions}")

        if not isinstance(user.penalty_questions, dict):
            user.penalty_questions = {}
            self.db.commit()

        selected_questions = []

        penalty_questions = []
        for q_text in user.penalty_questions:
            question = next(
                (q for q in self.questions if q["text"] == q_text), None
            )
            if question:
                penalty_questions.append(question)
                print(f"Added penalty question: {q_text} (attempts: {user.penalty_questions[q_text]})")

        selected_questions.extend(penalty_questions[:num_questions])

        remaining = num_questions - len(selected_questions)
        print(f"After penalties, need {remaining} more questions")

        if remaining > 0:
            if not user.question_bag:
                user.question_bag = [
                    q["text"]
                    for q in self.questions
                    if q["text"] not in user.penalty_questions
                ]
                self.db.commit()

            bag_questions = [
                q
                for q in self.questions
                if q["text"] in user.question_bag and q not in selected_questions
            ]

            if bag_questions:
                sampled = random.sample(
                    bag_questions, min(remaining, len(bag_questions))
                )
                selected_questions.extend(sampled)
                print(f"Added {len(sampled)} questions from bag")

        remaining = num_questions - len(selected_questions)
        if remaining > 0:
            available = [
                q
                for q in self.questions
                if q not in selected_questions
                and q["text"] not in user.penalty_questions
            ]
            sampled = random.sample(available, min(remaining, len(available)))
            selected_questions.extend(sampled)
            print(f"Added {len(sampled)} random questions")

        selected_questions = selected_questions[:num_questions]

        if shuffle_options:
            for question in selected_questions:
                combined = list(zip(question["options"], question["correct_answers"]))
                random.shuffle(combined)
                question["options"], question["correct_answers"] = zip(*combined)

        start_time = datetime.now()
        quiz = {
            "questions": selected_questions,
            "num_questions": len(selected_questions),
            "start_time": start_time.isoformat(),
            "subject": {  # Add complete subject info
                "code": self.subject.code,
                "name": self.subject.name
            }
        }

        print(f"Final quiz has {len(selected_questions)} questions")
        return quiz

    def grade_quiz(self, username: str, quiz: Dict, submitted_answers: Dict) -> Dict:
        try:
            start_time = datetime.fromisoformat(
                quiz.get("start_time", datetime.now().isoformat())
            )
            time_taken = (datetime.now() - start_time).total_seconds()

            correct_count = 0
            question_results = []

            user = self.get_user_progress(username)
            if not isinstance(user.penalty_questions, dict):
                user.penalty_questions = {}

            print(
                f"Initial state - Penalty questions: {user.penalty_questions}, Question bag: {user.question_bag}"
            )

            user = self.db.merge(self.get_user_progress(username))
            penalties = dict(user.penalty_questions or {})

            for i, question in enumerate(quiz["questions"]):
                question_number = str(i + 1)
                submitted = submitted_answers.get(question_number, [])

                if isinstance(submitted, str):
                    submitted = [submitted]
                elif not submitted:
                    submitted = ["No answer"]

                # Fix image path comparison by normalizing paths
                def normalize_path(path):
                    if isinstance(path, dict):
                        path = path["content"]
                    if isinstance(path, str):
                        # Remove leading '/' if present
                        return path.lstrip('/')
                    return path

                submitted_contents = [normalize_path(opt) for opt in submitted]
                correct_contents = [normalize_path(opt) for opt in question["correct_answers"]]

                is_correct = set(submitted_contents) != {"No answer"} and set(
                    submitted_contents
                ) == set(correct_contents)
                is_unanswered = set(submitted_contents) == {"No answer"}

                question_results.append(
                    {
                        "question": question["text"],
                        "submitted": submitted_contents,
                        "correct": correct_contents,
                        "is_correct": is_correct,
                        "is_unanswered": is_unanswered,
                    }
                )

                if is_correct:
                    correct_count += 1
                    if question["text"] in user.question_bag:
                        user.question_bag.remove(question["text"])
                    if question["text"] in penalties:
                        penalties[question["text"]] -= 1
                        if penalties[question["text"]] <= 0:
                            del penalties[question["text"]]
                            print(f"Penalty removed for: {question['text']}")
                        else:
                            print(
                                f"Penalty decremented for: {question['text']} -> {penalties[question['text']]}"
                            )
                else:
                    if question["text"] in user.question_bag:
                        user.question_bag.remove(question["text"])

                    current_attempts = penalties.get(question["text"], 0) + 1
                    penalties[question["text"]] = current_attempts
                    print(
                        f"Penalty incremented for: {question['text']} -> {current_attempts}"
                    )

            self.db.commit()

            user.penalty_questions = penalties
            self.db.commit()

            self.db.refresh(user)

            score = (correct_count / quiz["num_questions"]) * 100

            print(f"Final penalty questions: {user.penalty_questions}")

            test_history = TestHistory(
                user=user,
                score=score,
                time_taken=time_taken,
                questions={
                    "questions": quiz["questions"],
                    "answers": submitted_answers,
                    "results": question_results,
                },
            )
            self.db.add(test_history)
            self.db.commit()

            if user.active_quiz:
                self.db.delete(user.active_quiz)
                self.db.commit()

            results = {
                "score": score,
                "correct_count": correct_count,
                "total_questions": quiz["num_questions"],
                "question_results": question_results,
                "time_taken": time_taken,
                "subject": {  # Add subject information
                    "code": self.subject.code,
                    "name": self.subject.name
                }
            }
            logger.info(f"Quiz graded for user {username}. Score: {score}%")
            return results
        except Exception as e:
            logger.error(f"Error grading quiz for {username}: {e}")
            raise
