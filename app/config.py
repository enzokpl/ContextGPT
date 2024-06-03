# config.py
from dotenv import load_dotenv
import os

from openai import OpenAI

load_dotenv()  # Carrega as variáveis do arquivo .env

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'default_openai_api_key')
client = OpenAI()
project_dir = 'C:/projetos/SojaML'
