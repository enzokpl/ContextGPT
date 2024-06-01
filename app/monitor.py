import time
import requests
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

API_URL = "http://127.0.0.1:5000/context"


class ProjectFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            self.process(event)

    def on_created(self, event):
        if not event.is_directory:
            self.process(event)

    def process(self, event):
        file_path = event.src_path
        # Ignorar arquivos irrelevantes
        if self.should_ignore(file_path):
            return

        # Verificar se o arquivo existe antes de tentar ler
        if not os.path.exists(file_path):
            print(f"File does not exist: {file_path}")
            return

        try:
            content = self.read_file(file_path)
            if content is not None:
                data = {'file_path': file_path, 'content': content}
                response = requests.post(API_URL, json=data)
                if response.status_code == 200:
                    print(f"Updated context for {file_path}")
                else:
                    print(f"Failed to update context for {file_path}")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    def read_file(self, file_path):
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        print(f"Failed to read file {file_path} with available encodings.")
        return None

    def should_ignore(self, file_path):
        ignore_extensions = ['.lock', '.tmp', '.log']
        ignore_dirs = ['.git', '__pycache__', '.idea', 'venv']
        if any(file_path.endswith(ext) for ext in ignore_extensions):
            return True
        if any(dir in file_path for dir in ignore_dirs):
            return True
        return False


def start_monitoring(path):
    event_handler = ProjectFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
