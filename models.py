from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    JSON,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict, MutableList
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///quiz.db")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    question_bag = Column(MutableList.as_mutable(JSON))
    penalty_questions = Column(MutableDict.as_mutable(JSON))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    tests = relationship("TestHistory", back_populates="user", lazy="dynamic")
    active_quiz = relationship(
        "ActiveQuiz", back_populates="user", uselist=False, lazy="select"
    )
    quiz_results = relationship("QuizResult", back_populates="user", lazy="dynamic")

    Index("idx_username", "username")

    def __repr__(self):
        return f"<User {self.username}>"


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)  # e.g. 'AIL303m'
    name = Column(String)  # e.g. 'Artificial Intelligence'
    data_file = Column(String)  # e.g. 'quiz_data.csv'
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    tests = relationship("TestHistory", back_populates="subject", lazy="dynamic")
    active_quizzes = relationship(
        "ActiveQuiz", back_populates="subject", lazy="dynamic"
    )
    quiz_results = relationship("QuizResult", back_populates="subject", lazy="dynamic")

    Index("idx_subject_code", "code")


class TestHistory(Base):
    __tablename__ = "test_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float)
    time_taken = Column(Integer)
    questions = Column(JSON)
    completed_at = Column(DateTime, default=datetime.now)
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    user = relationship("User", back_populates="tests", lazy="select")
    subject = relationship("Subject", back_populates="tests", lazy="select")

    Index("idx_user_completed", "user_id", "completed_at")


class ActiveQuiz(Base):
    __tablename__ = "active_quizzes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    quiz_token = Column(String)
    quiz_data = Column(JSON)
    start_time = Column(DateTime, default=datetime.now)
    time_limit = Column(Integer, default=30)
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    user = relationship("User", back_populates="active_quiz", lazy="select")
    subject = relationship("Subject", back_populates="active_quizzes", lazy="select")

    Index("idx_quiz_token", "quiz_token")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    result_token = Column(String, unique=True)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    subject_id = Column(Integer, ForeignKey("subjects.id"))

    user = relationship("User", back_populates="quiz_results", lazy="select")
    subject = relationship("Subject", back_populates="quiz_results", lazy="select")

    Index("idx_result_token", "result_token")


# Initialize default subject after creating tables
def init_default_subjects(engine):
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        if not session.query(Subject).first():
            default_subject = Subject(
                code="AIL303m",
                name="Artificial Intelligence",
                data_file="quiz_data.csv",
            )
            session.add(default_subject)
            session.commit()


# Base.metadata.drop_all(engine) # Uncomment to drop all tables before creating new ones to avoid conflicts
Base.metadata.create_all(engine)
init_default_subjects(engine)
