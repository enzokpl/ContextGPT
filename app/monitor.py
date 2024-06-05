# monitor.py
import hashlib
import logging
import os
import time

import coloredlogs
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .cache import RedisCache
from .db import MongoDBConnector
from .embeddings import get_embedding

API_URL = "http://127.0.0.1:5000/context"
BACKUP_INTERVAL = 3600  # Intervalo de backup em segundos (1 hora)

# Configuração do logging
if not os.path.exists("logs"):
    os.makedirs("logs")

coloredlogs.install()

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


class ProjectFileHandler(FileSystemEventHandler):
    """
    Manipulador de eventos para arquivos de projeto.
    Processa eventos de modificação, criação e deleção de arquivos.
    """

    def __init__(self):
        super().__init__()

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
            with RedisCache() as cache:
                cached_hash = cache.get(file_path)
                if cached_hash == current_hash:
                    logging.info(f"File {file_path} has not changed, skipping processing.")
                    return

            content = self.read_file(file_path)
            if content is not None:
                embedding = get_embedding(content)
                data = {'file_path': file_path, 'embedding': embedding, 'content': content}

                with MongoDBConnector() as connector:
                    result = connector.insert_or_update_document(data)

                if result.matched_count > 0:  # Verifica se algum documento foi encontrado
                    if result.modified_count > 0:  # Verifica se houve modificação
                        logging.info(f"Contexto atualizado para {file_path}")
                    else:
                        logging.info(f"Arquivo {file_path} já existe na base de dados, nenhuma alteração realizada.")
                elif result.upserted_id is not None:  # Verifica se um novo documento foi inserido
                    logging.info(f"Contexto salvo para {file_path}")
                    print(f"Arquivo {file_path} adicionado na base de dados com sucesso!")

        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

    def handle_deleted_file(self, file_path):
        try:
            with MongoDBConnector() as connector:
                connector.delete_document(file_path)
            logging.info(f"Removed context for {file_path}")

            with RedisCache() as cache:
                cache.delete(file_path)
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
        ignore_dirs = ['.git', '__pycache__', '.idea', 'venv', 'data', '.venv']
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

    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
