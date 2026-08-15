"""
Couche d acces a la base de donnees MariaDB.
Design Pattern : SINGLETON (une seule instance du pool de connexions).
"""
from contextlib import contextmanager

import mariadb

from src.config.settings import Settings
from src.exceptions.domain_exceptions import ConnexionBDError, RequeteBDError
from src.utils.logger import logger


class DatabaseConnection:
    """Singleton encapsulant un pool de connexions MariaDB."""

    _instance = None
    _initialise = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not DatabaseConnection._initialise:
            self._pool = None
            DatabaseConnection._initialise = True

    def _creer_pool(self) -> None:
        """Initialise le pool de connexions (appel paresseux)."""
        Settings.valider()
        try:
            self._pool = mariadb.ConnectionPool(
                pool_name="stock_pool",
                pool_size=5,
                host=Settings.DB_HOST,
                port=Settings.DB_PORT,
                user=Settings.DB_USER,
                password=Settings.DB_PASSWORD,
                database=Settings.DB_NAME,
                autocommit=False,
            )
            logger.info("Pool MariaDB initialise -> %s", Settings.resume())
        except mariadb.Error as err:
            logger.critical("Echec init pool : %s", err)
            raise ConnexionBDError(
                f"Impossible de joindre {Settings.DB_HOST}:{Settings.DB_PORT} - {err}"
            ) from err

    def _obtenir_connexion(self):
        if self._pool is None:
            self._creer_pool()
        try:
            return self._pool.get_connection()
        except mariadb.Error as err:
            logger.error("Aucune connexion disponible : %s", err)
            raise ConnexionBDError(str(err)) from err

    @contextmanager
    def curseur(self, dictionnaire: bool = True, commit: bool = False):
        """Curseur SQL avec gestion automatique commit / rollback / fermeture."""
        conn = None
        cur = None
        try:
            conn = self._obtenir_connexion()
            cur = conn.cursor(dictionary=dictionnaire)
            yield cur
            if commit:
                conn.commit()
                logger.debug("Transaction validee (COMMIT).")
        except mariadb.Error as err:
            if conn:
                conn.rollback()
                logger.warning("Transaction annulee (ROLLBACK).")
            logger.error("Erreur SQL : %s", err)
            raise RequeteBDError(str(err)) from err
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    def tester_connexion(self) -> str:
        """Retourne la version du serveur si la connexion fonctionne."""
        with self.curseur() as cur:
            cur.execute("SELECT VERSION() AS version")
            version = cur.fetchone()["version"]
            logger.info("Connecte a MariaDB %s", version)
            return version


db = DatabaseConnection()
