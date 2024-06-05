# run.py
from app.api import app
from app.config import project_dir
from app.monitor import start_monitoring
import multiprocessing


def run_monitoring():
    """
    Inicia o monitoramento do diretório especificado.
    """
    start_monitoring(project_dir)


if __name__ == '__main__':
    # Iniciar a API Flask
    app.run(debug=True)

# todo - fazer com que as bases de dados iniciem automaticamente no "run", junto com o app.
