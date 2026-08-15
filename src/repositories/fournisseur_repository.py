"""Depot d'acces aux donnees des fournisseurs et entrepots."""
from src.exceptions.domain_exceptions import (DoublonError,
                                              FournisseurIntrouvableError)
from src.models.fournisseur import Fournisseur
from src.repositories.base_repository import BaseRepository
from src.utils.logger import logger


class FournisseurRepository(BaseRepository):
    """CRUD et recherches sur la table fournisseurs."""

    TABLE = "fournisseurs"

    def vers_entite(self, ligne):
        return Fournisseur(
            raison_sociale=ligne["raison_sociale"],
            contact=ligne.get("contact") or "",
            telephone=ligne.get("telephone") or "",
            email=ligne.get("email") or "",
            adresse=ligne.get("adresse") or "",
            ville=ligne.get("ville") or "",
            pays=ligne.get("pays") or "RDC",
            actif=bool(ligne.get("actif", True)),
            id_=ligne["id"],
            cree_le=ligne.get("cree_le"),
        )

    def rechercher(self, terme, actifs_seulement=True):
        """Recherche parametree sur plusieurs colonnes."""
        sql = f"""SELECT * FROM {self.TABLE}
                  WHERE (raison_sociale LIKE ? OR contact LIKE ?
                         OR ville LIKE ? OR email LIKE ?)"""
        motif = f"%{terme}%"
        params = [motif, motif, motif, motif]
        if actifs_seulement:
            sql += " AND actif = 1"
        sql += " ORDER BY raison_sociale LIMIT 100"

        with self.db.curseur() as cur:
            cur.execute(sql, tuple(params))
            return [self.vers_entite(l) for l in cur.fetchall()]

    def avec_nb_produits(self):
        """Fournisseurs enrichis du nombre de produits fournis."""
        with self.db.curseur() as cur:
            cur.execute("""
                SELECT f.*, COUNT(p.id) AS nb_produits,
                       COALESCE(SUM(p.prix_achat), 0) AS valeur_catalogue
                FROM fournisseurs f
                LEFT JOIN produits p ON p.fournisseur_id = f.id AND p.actif = 1
                GROUP BY f.id ORDER BY nb_produits DESC
            """)
            return [dict(l) for l in cur.fetchall()]

    def dictionnaire(self):
        """{id: raison_sociale} pour les menus deroulants."""
        with self.db.curseur() as cur:
            cur.execute(f"SELECT id, raison_sociale FROM {self.TABLE} "
                        "WHERE actif = 1 ORDER BY raison_sociale")
            return {l["id"]: l["raison_sociale"] for l in cur.fetchall()}

    def creer(self, fournisseur):
        fournisseur.valider()
        if self.existe("raison_sociale", fournisseur.raison_sociale):
            raise DoublonError("raison sociale", fournisseur.raison_sociale)
        donnees = fournisseur.to_dict()
        donnees.pop("id", None)
        fournisseur.id = self._inserer(donnees)
        logger.info("Fournisseur cree : %s", fournisseur.libelle())
        return fournisseur

    def modifier(self, fournisseur):
        fournisseur.valider()
        if self.existe("raison_sociale", fournisseur.raison_sociale,
                       exclure_id=fournisseur.id):
            raise DoublonError("raison sociale", fournisseur.raison_sociale)
        donnees = fournisseur.to_dict()
        donnees.pop("id", None)
        return self._mettre_a_jour(fournisseur.id, donnees)

    def trouver_par_id(self, identifiant):
        entite = super().trouver_par_id(identifiant)
        if entite is None:
            raise FournisseurIntrouvableError(identifiant)
        return entite


class EntrepotRepository(BaseRepository):
    """CRUD sur la table entrepots."""

    TABLE = "entrepots"

    def vers_entite(self, ligne):
        return dict(ligne)

    def dictionnaire(self):
        with self.db.curseur() as cur:
            cur.execute("SELECT id, nom FROM entrepots WHERE actif = 1 ORDER BY nom")
            return {l["id"]: l["nom"] for l in cur.fetchall()}

    def stock_par_entrepot(self):
        """Repartition des quantites et valeurs par entrepot."""
        with self.db.curseur() as cur:
            cur.execute("""
                SELECT e.id, e.nom, e.localisation,
                       COALESCE(SUM(s.quantite), 0) AS quantite,
                       COALESCE(SUM(s.quantite * p.prix_achat), 0) AS valeur,
                       COUNT(DISTINCT s.produit_id) AS nb_references
                FROM entrepots e
                LEFT JOIN stocks s ON s.entrepot_id = e.id
                LEFT JOIN produits p ON p.id = s.produit_id
                GROUP BY e.id ORDER BY valeur DESC
            """)
            return [dict(l) for l in cur.fetchall()]