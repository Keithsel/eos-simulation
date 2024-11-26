# EOS Simulation Platform

![image](https://github.com/user-attachments/assets/68925b1a-fd88-4f2d-9745-d56fd12b468b)

## Why Use This Platform?

As FPT students, preparing for the EOS final exam can be challenging without proper practice tools. This platform provides:

- A realistic exam environment simulation
- Practice opportunities before the real exam
- Progress tracking through quiz history
- Immediate feedback on performance

## Features

- Register and login to the platform
- Take mock quizzes in a simulated exam environment
- View the result of the quizzes
- View the history of the quizzes taken

## How Questions Are Managed

- The app shuffles the questions every time the user starts a new quiz.
- The app will not repeat questions that the user has already answered in the current quiz until the user has answered all the questions in the database.
- For questions answered incorrectly in previous quizzes, the app adds a "penalty" to the question, increasing the likelihood that the user will see these questions more often in subsequent quizzes.

## Setup Guide

### Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)

### Quick Start

1. Get the code and setup environment:

```bash
git clone https://github.com/Keithsel/eos-simulation.git && cd eos-simulation
```

2. Set up Python environment: (optional, but recommended)

- Choose ONE of these options:

```bash
# Option A: Using venv (recommended for most users)
python3 -m venv venv
source venv/bin/activate

# Option B: Using virtualenv
pip install virtualenv
virtualenv venv
source venv/bin/activate

# Option C: Using conda
conda create --name venv
conda activate venv
```

3. Install dependencies

  ```bash
  pip install -r requirements.txt
  ```

4. Run the app

  ```bash
  python app.py
  ```

5. Access the platform

- Open your browser
- Visit `http://127.0.0.1:5000/`
- You should see the login page

### Database Management

The application uses an SQLite database (`quiz.db`) stored in the project root. To reset it:

- Either delete the `quiz.db` file
- Or uncomment this line in `models.py`:

  ```python
  #Base.metadata.drop_all(engine)
  ```

- Start the app once
- Re-comment the line to prevent accidental resets

### Development Notes

- The app runs in debug mode for development
- Code changes reflect immediately without restart
- Database changes require manual reset as described above
