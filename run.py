from app.api import app
from app.config import project_dir
from app.monitor import start_monitoring
import threading


def run_monitoring():
    """
    Inicia o monitoramento do diretório especificado.
    """
    start_monitoring(project_dir)


if __name__ == '__main__':
    # Iniciar monitoramento em uma thread separada
    monitor_thread = threading.Thread(target=run_monitoring)
    monitor_thread.start()

    # Iniciar a API Flask
    app.run(debug=True)
