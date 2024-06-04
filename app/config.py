# config.py
from dotenv import load_dotenv
import os

from openai import OpenAI

load_dotenv()  # Carrega as variáveis do arquivo .env

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'default_openai_api_key')

client = OpenAI()

project_dir = 'C:/projetos/SojaML'

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")  # URI de conexão
DATABASE_NAME = os.getenv("DATABASE_NAME", "contextgpt")  # Nome do banco de dados
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "embeddings")  # Nome da coleção

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
