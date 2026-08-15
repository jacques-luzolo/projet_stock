"""Service d'authentification et de gestion des sessions."""
from src.exceptions.domain_exceptions import (AuthentificationError,
                                              CompteDesactiveError,
                                              PermissionRefuseeError)
from src.repositories.utilisateur_repository import (RoleRepository,
                                                     UtilisateurRepository)
from src.utils.logger import logger
from src.utils.security import (hacher_mot_de_passe, valider_force_mot_de_passe,
                                verifier_mot_de_passe)


class AuthService:
    """Authentification, autorisation et gestion des comptes."""

    def __init__(self):
        self.depot = UtilisateurRepository()
        self.depot_roles = RoleRepository()

    def authentifier(self, login, mot_de_passe):
        """
        Verifie les identifiants et retourne l'utilisateur (sous-classe
        correspondant a son role grace au polymorphisme).
        """
        if not login or not mot_de_passe:
            raise AuthentificationError("Login et mot de passe obligatoires.")

        utilisateur = self.depot.trouver_par_login(login)
        if utilisateur is None:
            logger.warning("Tentative de connexion, login inconnu : %s", login)
            raise AuthentificationError()

        if not verifier_mot_de_passe(mot_de_passe, utilisateur.mot_de_passe_hash):
            logger.warning("Mot de passe incorrect pour : %s", login)
            raise AuthentificationError()

        if not utilisateur.actif:
            raise CompteDesactiveError(login)

        self.depot.enregistrer_connexion(utilisateur.id)
        logger.info("Connexion reussie : %s (%s)", login, utilisateur.role())
        return utilisateur

    @staticmethod
    def verifier_permission(utilisateur, action):
        """Leve une exception si l'utilisateur n'a pas le droit."""
        if utilisateur is None:
            raise AuthentificationError("Session expiree, reconnectez-vous.")
        if not utilisateur.peut(action):
            raise PermissionRefuseeError(utilisateur.role(), action)
        return True

    def creer_compte(self, nom, prenom, email, login, mot_de_passe, role):
        """Cree un nouvel utilisateur avec mot de passe hache."""
        valider_force_mot_de_passe(mot_de_passe)
        role_id = self.depot_roles.id_par_nom(role)
        if role_id is None:
            raise AuthentificationError(f"Role inconnu : {role}")

        from src.models.utilisateur import creer_utilisateur_par_role
        utilisateur = creer_utilisateur_par_role(
            role, nom=nom, prenom=prenom, email=email, login=login,
            mot_de_passe_hash=hacher_mot_de_passe(mot_de_passe),
            role_id=role_id,
        )
        return self.depot.creer(utilisateur)

    def changer_mot_de_passe(self, utilisateur_id, ancien, nouveau):
        utilisateur = self.depot.trouver_par_id(utilisateur_id)
        if utilisateur is None:
            raise AuthentificationError("Utilisateur introuvable.")
        if not verifier_mot_de_passe(ancien, utilisateur.mot_de_passe_hash):
            raise AuthentificationError("Ancien mot de passe incorrect.")
        valider_force_mot_de_passe(nouveau)
        self.depot.changer_mot_de_passe(utilisateur_id, hacher_mot_de_passe(nouveau))
        logger.info("Mot de passe modifie pour l'utilisateur %s", utilisateur_id)
        return True

    def lister_utilisateurs(self):
        return self.depot.lister()

    def basculer_activation(self, utilisateur_id, actif):
        return (self.depot.reactiver(utilisateur_id) if actif
                else self.depot.desactiver(utilisateur_id))