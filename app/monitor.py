# monitor.py
import os
import time
import hashlib
import json
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer  # Correção da importação
import requests
from .embeddings import get_embedding

API_URL = "http://127.0.0.1:5000/context"
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "file_cache.json")
BACKUP_FILE = os.path.join(CACHE_DIR, "file_cache_backup.json")
BACKUP_INTERVAL = 3600  # Intervalo de backup em segundos (1 hora)

# Configuração do logging
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[
    logging.FileHandler("logs/file_monitor.log"),
    logging.StreamHandler()
])


def calculate_file_hash(file_path):
    """
    Calcula o hash SHA-256 do conteúdo de um arquivo.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def load_cache():
    """
    Carrega o cache de um arquivo JSON.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """
    Salva o cache em um arquivo JSON.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


def backup_cache():
    """
    Faz backup do cache em um arquivo JSON.
    """
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache_data = f.read()
        with open(BACKUP_FILE, 'w') as f:
            f.write(cache_data)
        logging.info("Cache backup realizado com sucesso.")

    # Reagenda o próximo backup
    Timer(BACKUP_INTERVAL, backup_cache).start()


class ProjectFileHandler(FileSystemEventHandler):
    """
    Manipulador de eventos para arquivos de projeto.
    Processa eventos de modificação, criação e deleção de arquivos.
    """

    def __init__(self):
        super().__init__()
        self.cache = load_cache()

    def on_modified(self, event):
        if not event.is_directory:
            logging.info(f"Modified file detected: {event.src_path}")
            self.process(event, "modified")

    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"Created file detected: {event.src_path}")
            self.process(event, "created")

    def on_deleted(self, event):
        if not event.is_directory:
            logging.info(f"Deleted file detected: {event.src_path}")
            self.process(event, "deleted")

    def process(self, event, event_type):
        file_path = event.src_path
        if self.should_ignore(file_path):
            return

        if event_type == "deleted":
            self.handle_deleted_file(file_path)
            return

        if not os.path.exists(file_path):
            logging.warning(f"File does not exist: {file_path}")
            return

        self.process_file(file_path)

    def process_file(self, file_path):
        try:
            current_hash = calculate_file_hash(file_path)
            if file_path in self.cache and self.cache[file_path]['hash'] == current_hash:
                logging.info(f"File {file_path} has not changed, skipping processing.")
                return

            content = self.read_file(file_path)
            if content is not None:
                embedding = get_embedding(content)
                self.cache[file_path] = {'hash': current_hash, 'embedding': embedding, 'content': content}
                save_cache(self.cache)
                data = {'file_path': file_path, 'embedding': embedding, 'content': content}
                response = requests.post(API_URL, json=data)
                if response.status_code == 200:
                    logging.info(f"Updated context for {file_path}")
                else:
                    logging.error(f"Failed to update context for {file_path}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

    def handle_deleted_file(self, file_path):
        try:
            response = requests.delete(f"{API_URL}/{file_path}")
            if response.status_code == 200:
                logging.info(f"Removed context for {file_path}")
                if file_path in self.cache:
                    del self.cache[file_path]
                    save_cache(self.cache)
            else:
                logging.error(f"Failed to remove context for {file_path}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error removing context for file {file_path}: {e}")

    def read_file(self, file_path):
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue
        logging.error(f"Failed to read file {file_path} with available encodings.")
        return None

    def should_ignore(self, file_path):
        ignore_extensions = ['.lock', '.tmp', '.log']
        ignore_dirs = ['.git', '__pycache__', '.idea', 'venv', 'data']
        if any(file_path.endswith(ext) for ext in ignore_extensions):
            return True
        if any(dir in file_path for dir in ignore_dirs):
            return True
        return False


def process_existing_files(path, handler):
    """
    Processa todos os arquivos existentes no diretório monitorado.
    Percorre o diretório e chama o manipulador de eventos para cada arquivo.
    """
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            # Verificar se o arquivo deve ser ignorado
            if handler.should_ignore(file_path):
                continue
            # Processar o arquivo existente
            handler.process_file(file_path)


class FileEvent:
    """
    Classe para simular um evento de arquivo.
    Utilizada para processar arquivos existentes no início do monitoramento.
    """

    def __init__(self, src_path):
        self.src_path = src_path
        self.is_directory = False


def start_monitoring(path):
    """
    Inicia o monitoramento do diretório especificado.
    Configura o observador de arquivos e processa arquivos existentes.
    """
    event_handler = ProjectFileHandler()
    # Processar todos os arquivos existentes no diretório monitorado
    process_existing_files(path, event_handler)

    # Inicia o backup periódico do cache
    backup_cache()

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
