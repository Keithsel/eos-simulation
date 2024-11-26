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

### Experimental Features

> ⚠️ **Temporary Feature**: Coursera Quiz Parser
>
> I've added an experimental feature that allows parsing quiz data directly from Coursera pages. This is currently in testing and I will make a Firefox (maybe Chrome) extension for easier use. To try it:
>
> 1. Install the `watchdog` package:
>
> ```bash
> pip install watchdog
> ```
>
> 2. Run the watcher script:
>
> ```bash
> python watch_and_move.py
> ```
>
> 3. Open the Coursera quiz page in your browser, suppose that you have completed the quiz. Press "View submission" and wait for the view submission page to load.
>
> 4. Press F12 or Ctrl+Shift+I to open the developer console. Copy the code in `parse_qna_coursera.js` and paste it into the console.
>
> 5. Press Enter. The console will download a JSON file of the quiz data to the downloads folder defined by the browser, and the watcher script will move the file to the folder you specified in the watcher script.
>
> Why the watcher script? Browser console can't access the local filesystem, so the script is a workaround to move the downloaded file to the app's folder.
