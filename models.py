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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tests = relationship("TestHistory", back_populates="user")
    active_quiz = relationship("ActiveQuiz", back_populates="user", uselist=False)

    Index("idx_username", "username")

    def __repr__(self):
        return f"<User {self.username}>"


class TestHistory(Base):
    __tablename__ = "test_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float)
    time_taken = Column(Integer)
    questions = Column(JSON)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tests")

    Index("idx_user_completed", "user_id", "completed_at")


class ActiveQuiz(Base):
    __tablename__ = "active_quizzes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    quiz_token = Column(String)
    quiz_data = Column(JSON)
    start_time = Column(DateTime, default=datetime.utcnow)
    time_limit = Column(Integer, default=30)

    user = relationship("User", back_populates="active_quiz")

    Index("idx_quiz_token", "quiz_token")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    result_token = Column(String, unique=True)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

    user = relationship("User", backref="quiz_results")

    Index("idx_result_token", "result_token")


# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
