# eos-simulation

![image](https://github.com/user-attachments/assets/68925b1a-fd88-4f2d-9745-d56fd12b468b)

## Description

As FPT students take the final exam on EOS, we don't have any tool to practice before the exam, while replicating the exam environment has always been proven to be the best way to prepare for the exam. This project aims to provide a platform for students to practice for the EOS exam by taking mock quizzes in a simulated exam environment.

## Features

- Register and login to the platform
- Take mock quizzes in a simulated exam environment
- View the result of the quizzes
- View the history of the quizzes taken

## Tech stack

- Frontend: Jinja2, HTML, CSS, JavaScript
- Backend: Flask
- Database: SQLite

## Setup

1. Create and activate virtual environment (optional, but recommended)

- If you are using `venv`:

```bash
python3 -m venv venv
source venv/bin/activate
```

- If you are using `virtualenv` (install it via `pip install virtualenv`):

```bash
virtualenv venv
source venv/bin/activate
```

- If you are using `conda`:

```bash
conda create --name venv
conda activate venv
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app

```bash
python app.py
```

4. Open your browser and go to `http://127.0.0.1:5000/`, you should see the app running

### Note

- The app is running in debug mode, so you can see the changes immediately after you save the file
- The database is created in the root directory of the project, named `quiz.db`. To purge the database, simply delete this file, or uncomment line 128 in the `models.py` file:
  
  ```python
  #Base.metadata.drop_all(engine)
  ```
  Run the app once, then comment this line again to prevent the database from being purged every time you run the app.