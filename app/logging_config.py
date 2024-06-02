import structlog
import logging
from logging.config import dictConfig

# Configuração básica do logging
logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/application.log")
    ]
)


def configure_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO", utc=True),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )


configure_logging()
