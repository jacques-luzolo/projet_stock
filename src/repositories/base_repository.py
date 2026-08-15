"""
Design Pattern : REPOSITORY (DAO - Data Access Object).

Probleme resolu :
    Les classes metier (Produit, Fournisseur...) ne doivent pas contenir
    de SQL. Inversement, changer de SGBD ne doit pas impacter le metier.

Solution :
    Une couche intermediaire qui traduit objets <-> lignes de table.
    Toutes les requetes sont PARAMETREES (protection injection SQL).
"""
from abc import ABC, abstractmethod

from src.database.connection import db
from src.utils.logger import logger


class BaseRepository(ABC):
    """
    Depot generique fournissant les operations CRUD communes.

    Les classes filles doivent definir :
      - TABLE       : nom de la table SQL
      - vers_entite : conversion d'une ligne SQL en objet metier
    """

    TABLE = None
    CLE_PRIMAIRE = "id"

    def __init__(self):
        self.db = db
        if not self.TABLE:
            raise ValueError(f"{type(self).__name__} doit definir TABLE")

    # ------------------------------------------------------ abstrait
    @abstractmethod
    def vers_entite(self, ligne):
        """Transforme un dictionnaire SQL en objet metier."""
        raise NotImplementedError

    # ------------------------------------------------------ lecture
    def lister(self, actifs_seulement=False, limite=None):
        """Retourne toutes les entites de la table."""
        sql = f"SELECT * FROM {self.TABLE}"
        params = []
        if actifs_seulement:
            sql += " WHERE actif = 1"
        sql += f" ORDER BY {self.CLE_PRIMAIRE} DESC"
        if limite:
            sql += " LIMIT ?"
            params.append(int(limite))

        with self.db.curseur() as cur:
            cur.execute(sql, tuple(params))
            return [self.vers_entite(l) for l in cur.fetchall()]

    def trouver_par_id(self, identifiant):
        """Retourne une entite par son identifiant, ou None."""
        sql = f"SELECT * FROM {self.TABLE} WHERE {self.CLE_PRIMAIRE} = ?"
        with self.db.curseur() as cur:
            cur.execute(sql, (identifiant,))
            ligne = cur.fetchone()
            return self.vers_entite(ligne) if ligne else None

    def compter(self, actifs_seulement=False):
        """Nombre total d'enregistrements."""
        sql = f"SELECT COUNT(*) AS total FROM {self.TABLE}"
        if actifs_seulement:
            sql += " WHERE actif = 1"
        with self.db.curseur() as cur:
            cur.execute(sql)
            return cur.fetchone()["total"]

    def existe(self, champ, valeur, exclure_id=None):
        """Verifie l'existence d'une valeur (controle des doublons)."""
        sql = f"SELECT COUNT(*) AS n FROM {self.TABLE} WHERE {champ} = ?"
        params = [valeur]
        if exclure_id:
            sql += f" AND {self.CLE_PRIMAIRE} <> ?"
            params.append(exclure_id)
        with self.db.curseur() as cur:
            cur.execute(sql, tuple(params))
            return cur.fetchone()["n"] > 0

    # ------------------------------------------------------ ecriture
    def _inserer(self, donnees):
        """Insertion generique a partir d'un dictionnaire."""
        colonnes = ", ".join(donnees.keys())
        marqueurs = ", ".join(["?"] * len(donnees))
        sql = f"INSERT INTO {self.TABLE} ({colonnes}) VALUES ({marqueurs})"

        with self.db.curseur(commit=True) as cur:
            cur.execute(sql, tuple(donnees.values()))
            nouvel_id = cur.lastrowid
            logger.info("INSERT %s id=%s", self.TABLE, nouvel_id)
            return nouvel_id

    def _mettre_a_jour(self, identifiant, donnees):
        """Mise a jour generique."""
        if not donnees:
            return False
        affectations = ", ".join(f"{c} = ?" for c in donnees)
        sql = (f"UPDATE {self.TABLE} SET {affectations} "
               f"WHERE {self.CLE_PRIMAIRE} = ?")
        params = tuple(donnees.values()) + (identifiant,)

        with self.db.curseur(commit=True) as cur:
            cur.execute(sql, params)
            logger.info("UPDATE %s id=%s (%s ligne(s))",
                        self.TABLE, identifiant, cur.rowcount)
            return cur.rowcount > 0

    def supprimer(self, identifiant):
        """Suppression physique de l'enregistrement."""
        sql = f"DELETE FROM {self.TABLE} WHERE {self.CLE_PRIMAIRE} = ?"
        with self.db.curseur(commit=True) as cur:
            cur.execute(sql, (identifiant,))
            logger.warning("DELETE %s id=%s", self.TABLE, identifiant)
            return cur.rowcount > 0

    def desactiver(self, identifiant):
        """Suppression logique : on conserve l'historique."""
        return self._mettre_a_jour(identifiant, {"actif": 0})

    def reactiver(self, identifiant):
        """Reactive un enregistrement desactive."""
        return self._mettre_a_jour(identifiant, {"actif": 1})

    # ------------------------------------------------------ utilitaire
    def executer(self, sql, params=(), commit=False):
        """
        Execute une requete personnalisee (toujours parametree).
        Utile pour les vues et les jointures complexes.
        """
        with self.db.curseur(commit=commit) as cur:
            cur.execute(sql, params)
            if sql.strip().upper().startswith("SELECT"):
                return cur.fetchall()
            return cur.rowcount