"""Configuration centralisee : charge les variables du fichier .env"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


class Settings:
    """Parametres applicatifs (lecture seule)."""

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "gestion_stock")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    APP_NAME: str = os.getenv("APP_NAME", "StockManager")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    BASE_DIR: Path = BASE_DIR
    LOG_DIR: Path = BASE_DIR / "logs"
    SQL_DIR: Path = BASE_DIR / "sql"

    @classmethod
    def valider(cls) -> None:
        """Verifie que la configuration minimale est presente."""
        manquants = [c for c in ("DB_HOST", "DB_NAME", "DB_USER") if not getattr(cls, c)]
        if manquants:
            raise ValueError(f"Configuration incomplete : {', '.join(manquants)}")

    @classmethod
    def resume(cls) -> str:
        """Resume lisible (sans mot de passe)."""
        return f"{cls.APP_NAME} | BD: {cls.DB_USER}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
