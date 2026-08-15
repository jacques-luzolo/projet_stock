"""Systeme de journalisation de l application."""
import logging
from logging.handlers import RotatingFileHandler

from src.config.settings import Settings

Settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(Settings.APP_NAME)
logger.setLevel(getattr(logging, Settings.LOG_LEVEL.upper(), logging.INFO))
logger.propagate = False

if not logger.handlers:
    formatteur = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler_fichier = RotatingFileHandler(
        Settings.LOG_DIR / "app.log", maxBytes=1000000, backupCount=5, encoding="utf-8"
    )
    handler_fichier.setFormatter(formatteur)

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formatteur)

    logger.addHandler(handler_fichier)
    logger.addHandler(handler_console)
