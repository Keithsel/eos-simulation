import json
import os
from sqlalchemy.orm import sessionmaker
from .models import engine, Subject
from typing import Optional, Dict


def extract_subject_code(filename: str) -> str:
    """Extract subject code from CSV filename."""
    return os.path.splitext(filename)[0].upper()


def get_curriculum_data() -> Dict:
    """Load curriculum data from JSON file"""
    curriculum_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "curriculum",
        "BIT_AI_K18B-18C.json",
    )
    with open(curriculum_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_subject_name(subject_data: Dict) -> str:
    """Extract English name or full name from subject data"""
    name = subject_data["name"]
    if name.get("en"):
        return name["en"]
    return name.get("full", name.get("vi", ""))


def check_data_file(subject_code: str) -> Optional[str]:
    """Check if data file exists for subject code"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "bank")
    possible_files = [f"{subject_code}.csv", f"{subject_code.lower()}.csv"]

    for file in possible_files:
        if os.path.exists(os.path.join(data_dir, file)):
            return file
    return None


def add_subject(
    subject_code: str, name: str = None, data_file: str = None
) -> Optional[Subject]:
    """Add a subject to the database if it has a corresponding data file"""
    Session = sessionmaker(bind=engine)
    session = Session()

    existing = session.query(Subject).filter_by(code=subject_code).first()
    if existing:
        print(f"Subject {subject_code} already exists")
        session.close()
        return existing

    # If no data file specified, try to find it
    if not data_file:
        data_file = check_data_file(subject_code)
        if not data_file:
            # print(f"No data file found for subject {subject_code}")
            session.close()
            return None

    subject = Subject(code=subject_code, name=name or subject_code, data_file=data_file)

    session.add(subject)
    session.commit()
    print(f"Added subject: {subject_code} - {name}")
    session.close()
    return subject


def init_subjects_from_curriculum():
    """Initialize subjects from curriculum data"""
    curriculum = get_curriculum_data()

    for subject in curriculum["subjects"]:
        code = subject["code"]
        name = get_subject_name(subject)

        # Skip subjects that are just placeholders (like AI17_COM*1)
        if "*" in code:
            continue

        add_subject(code, name)


if __name__ == "__main__":
    init_subjects_from_curriculum()
