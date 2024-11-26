
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import shutil

class QuizFileHandler(FileSystemEventHandler):
    def __init__(self, target_dir):
        self.target_dir = target_dir

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('quiz_data.json'):
            os.makedirs(self.target_dir, exist_ok=True)
            
            time.sleep(1)
            
            filename = os.path.basename(event.src_path)
            target_path = os.path.join(self.target_dir, filename)
            
            base, ext = os.path.splitext(target_path)
            counter = 1
            while os.path.exists(target_path):
                target_path = f"{base}({counter}){ext}"
                counter += 1
            
            shutil.move(event.src_path, target_path)
            print(f"Moved {filename} to {target_path}")

def watch_directory(source_dir, target_dir):
    event_handler = QuizFileHandler(target_dir)
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()
    
    try:
        print(f"Watching {source_dir} for quiz_data.json files...")
        print(f"Will move them to {target_dir}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped watching directory")
    observer.join()

if __name__ == "__main__":
    downloads_dir = os.path.expanduser("~/Inbox")
    target_dir = os.path.expanduser("~/Documents/GitHub/personal/exam-mock/proc")
    watch_directory(downloads_dir, target_dir)