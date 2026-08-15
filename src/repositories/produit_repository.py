"""Depot d'acces aux donnees des produits et des categories."""
from src.exceptions.domain_exceptions import (DoublonError,
                                              ProduitIntrouvableError)
from src.models.produit import Categorie
from src.patterns.factory import ProduitFactory
from src.repositories.base_repository import BaseRepository
from src.utils.logger import logger


class ProduitRepository(BaseRepository):
    """CRUD et recherches sur la table produits."""

    TABLE = "produits"

    def vers_entite(self, ligne):
        """Delegue la construction a la fabrique (pattern Factory)."""
        return ProduitFactory.creer(dict(ligne))

    # ------------------------------------------------------- lectures
    def lister_avec_stock(self, actifs_seulement=True):
        """
        Liste les produits avec leur quantite totale,
        en s'appuyant sur la vue SQL v_stock_global.
        """
        sql = "SELECT * FROM v_stock_global"
        if actifs_seulement:
            sql += " WHERE actif = 1"
        sql += " ORDER BY designation"

        with self.db.curseur() as cur:
            cur.execute(sql)
            return [dict(l) for l in cur.fetchall()]

    def trouver_par_reference(self, reference):
        """Retourne un produit par sa reference unique."""
        sql = f"SELECT * FROM {self.TABLE} WHERE reference = ?"
        with self.db.curseur() as cur:
            cur.execute(sql, (reference.strip().upper(),))
            ligne = cur.fetchone()
            if not ligne:
                raise ProduitIntrouvableError(reference)
            return self.vers_entite(ligne)

    def rechercher(self, terme, categorie_id=None, actifs_seulement=True):
        """
        Recherche parametree (protection contre l'injection SQL).
        Le terme saisi par l'utilisateur est passe en PARAMETRE,
        jamais concatene dans la requete.
        """
        sql = f"""SELECT * FROM {self.TABLE}
                  WHERE (designation LIKE ? OR reference LIKE ?
                         OR description LIKE ?)"""
        motif = f"%{terme}%"
        params = [motif, motif, motif]

        