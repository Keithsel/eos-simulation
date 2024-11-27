import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import shutil


class BaseFileHandler(FileSystemEventHandler):
    def __init__(self, target_dir):
        self.target_dir = target_dir

    def move_file(self, src_path):
        os.makedirs(self.target_dir, exist_ok=True)
        time.sleep(1)

        filename = os.path.basename(src_path)
        target_path = os.path.join(self.target_dir, filename)

        base, ext = os.path.splitext(target_path)
        counter = 1
        while os.path.exists(target_path):
            target_path = f"{base}({counter}){ext}"
            counter += 1

        shutil.move(src_path, target_path)
        print(f"Moved {filename} to {target_path}")


class QuizFileHandler(BaseFileHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith("quiz_data.json"):
            self.move_file(event.src_path)


class CurriculumFileHandler(BaseFileHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            filename = os.path.basename(event.src_path)
            if filename.startswith("B"):
                self.move_file(event.src_path)


def watch_directory(source_dir, handlers):
    observer = Observer()
    for handler in handlers:
        observer.schedule(handler, source_dir, recursive=False)
    observer.start()

    try:
        print(f"Watching {source_dir} for files...")
        for handler in handlers:
            print(f"Using handler: {handler.__class__.__name__}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped watching directory")
    observer.join()


if __name__ == "__main__":
    downloads_dir = os.path.expanduser("~/Inbox")
    base_dir = os.path.expanduser("~/Documents/GitHub/personal/exam-mock")
    quiz_dir = os.path.join(base_dir, "proc/new")
    curriculum_dir = os.path.join(base_dir, "data/curriculum")

    handlers = [QuizFileHandler(quiz_dir), CurriculumFileHandler(curriculum_dir)]
    watch_directory(downloads_dir, handlers)
