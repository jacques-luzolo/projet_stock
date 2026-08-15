"""Depot d'acces aux donnees des utilisateurs et des roles."""
from datetime import datetime

from src.exceptions.domain_exceptions import DoublonError
from src.models.utilisateur import creer_utilisateur_par_role
from src.repositories.base_repository import BaseRepository
from src.utils.logger import logger


class UtilisateurRepository(BaseRepository):
    """CRUD sur la table utilisateurs (avec jointure sur les roles)."""

    TABLE = "utilisateurs"

    def vers_entite(self, ligne):
        """
        Instancie la bonne sous-classe (Admin / Gestionnaire / Vendeur)
        grace a la fabrique : POLYMORPHISME automatique.
        """
        return creer_utilisateur_par_role(
            ligne.get("role_nom") or "invite",
            nom=ligne["nom"],
            prenom=ligne.get("prenom") or "",
            email=ligne.get("email") or "",
            login=ligne["login"],
            mot_de_passe_hash=ligne["mot_de_passe_hash"],
            role_id=ligne.get("role_id"),
            actif=bool(ligne.get("actif", True)),
            derniere_connexion=ligne.get("derniere_connexion"),
            id_=ligne["id"],
            cree_le=ligne.get("cree_le"),
        )

    _SELECT = """SELECT u.*, r.nom AS role_nom
                 FROM utilisateurs u
                 JOIN roles r ON r.id = u.role_id"""

    def lister(self, actifs_seulement=False, limite=None):
        sql = self._SELECT
        if actifs_seulement:
            sql += " WHERE u.actif = 1"
        sql += " ORDER BY r.id, u.nom"
        with self.db.curseur() as cur:
            cur.execute(sql)
            return [self.vers_entite(l) for l in cur.fetchall()]

    def trouver_par_login(self, login):
        """Utilise par l'authentification."""
        with self.db.curseur() as cur:
            cur.execute(self._SELECT + " WHERE u.login = ?",
                        ((login or "").strip().lower(),))
            ligne = cur.fetchone()
            return self.vers_entite(ligne) if ligne else None

    def trouver_par_id(self, identifiant):
        with self.db.curseur() as cur:
            cur.execute(self._SELECT + " WHERE u.id = ?", (identifiant,))
            ligne = cur.fetchone()
            return self.vers_entite(ligne) if ligne else None

    def enregistrer_connexion(self, utilisateur_id):
        return self._mettre_a_jour(utilisateur_id,
                                   {"derniere_connexion": datetime.now()})

    def creer(self, utilisateur):
        utilisateur.valider()
        if self.existe("login", utilisateur.login):
            raise DoublonError("login", utilisateur.login)
        if utilisateur.email and self.existe("email", utilisateur.email):
            raise DoublonError("email", utilisateur.email)

        donnees = {
            "nom": utilisateur.nom,
            "prenom": utilisateur.prenom,
            "email": utilisateur.email,
            "login": utilisateur.login,
            "mot_de_passe_hash": utilisateur.mot_de_passe_hash,
            "role_id": utilisateur.role_id,
            "actif": int(utilisateur.actif),
        }
        utilisateur.id = self._inserer(donnees)
        logger.info("Utilisateur cree : %s", utilisateur.libelle())
        return utilisateur

    def modifier(self, utilisateur):
        donnees = {
            "nom": utilisateur.nom,
            "prenom": utilisateur.prenom,
            "email": utilisateur.email,
            "role_id": utilisateur.role_id,
            "actif": int(utilisateur.actif),
        }
        return self._mettre_a_jour(utilisateur.id, donnees)

    def changer_mot_de_passe(self, utilisateur_id, nouveau_hash):
        return self._mettre_a_jour(utilisateur_id,
                                   {"mot_de_passe_hash": nouveau_hash})


class RoleRepository(BaseRepository):
    """Lecture de la table roles."""

    TABLE = "roles"

    def vers_entite(self, ligne):
        return dict(ligne)

    def dictionnaire(self):
        with self.db.curseur() as cur:
            cur.execute("SELECT id, nom FROM roles ORDER BY id")
            return {l["id"]: l["nom"] for l in cur.fetchall()}

    def id_par_nom(self, nom):
        with self.db.curseur() as cur:
            cur.execute("SELECT id FROM roles WHERE nom = ?", (nom,))
            ligne = cur.fetchone()
            return ligne["id"] if ligne else None