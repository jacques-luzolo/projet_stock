"""
Modeles Utilisateur et ses specialisations par role.

Concepts POO demontres :
- HERITAGE EN CASCADE : Utilisateur -> Vendeur -> Gestionnaire -> Admin
                        Chaque niveau AJOUTE des permissions au precedent.
- POLYMORPHISME       : permissions() et peut() donnent des resultats
                        differents selon la classe reelle de l'objet,
                        alors que le code appelant est identique.
- ENCAPSULATION       : le hash du mot de passe reste prive.
"""
from src.exceptions.domain_exceptions import ValidationError
from src.models.base import EntiteBase
from src.utils.security import valider_email


class Utilisateur(EntiteBase):
    """Utilisateur generique de l'application (classe mere)."""

    ROLE = "invite"

    def __init__(self, nom, prenom="", email="", login="", mot_de_passe_hash="",
                 role_id=None, actif=True, derniere_connexion=None,
                 id_=None, cree_le=None):
        super().__init__(id_, cree_le)

        # Attributs prives
        self.__nom = ""
        self.__login = ""
        self.__email = ""
        self.__mot_de_passe_hash = ""

        # Affectation via les setters
        self.nom = nom
        self.login = login
        self.email = email
        self.mot_de_passe_hash = mot_de_passe_hash

        # Attributs publics
        self.prenom = prenom
        self.role_id = role_id
        self.actif = actif
        self.derniere_connexion = derniere_connexion

    # -------------------------------------------------------------- nom
    @property
    def nom(self):
        return self.__nom

    @nom.setter
    def nom(self, valeur):
        valeur = (valeur or "").strip()
        if len(valeur) < 2:
            raise ValidationError("nom", "2 caracteres minimum")
        self.__nom = valeur

    # ------------------------------------------------------------ login
    @property
    def login(self):
        return self.__login

    @login.setter
    def login(self, valeur):
        valeur = (valeur or "").strip().lower()
        if len(valeur) < 3:
            raise ValidationError("login", "3 caracteres minimum")
        self.__login = valeur

    # ------------------------------------------------------------ email
    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, valeur):
        valeur = (valeur or "").strip()
        if valeur:
            valider_email(valeur)
        self.__email = valeur

    # ------------------------------------------------- mot de passe hash
    @property
    def mot_de_passe_hash(self):
        """Seul le hash est accessible, jamais le mot de passe en clair."""
        return self.__mot_de_passe_hash

    @mot_de_passe_hash.setter
    def mot_de_passe_hash(self, valeur):
        self.__mot_de_passe_hash = valeur or ""

    # ------------------------------------------------------ POLYMORPHISME
    def permissions(self):
        """
        Ensemble des actions autorisees.
        Chaque sous-classe enrichit cet ensemble.
        """
        return {"consulter_dashboard"}

    def peut(self, action):
        """
        Interface commune a tous les roles.
        Le resultat depend de la classe reelle de l'objet (polymorphisme).
        """
        return action in self.permissions()

    def role(self):
        return self.ROLE

    def nom_complet(self):
        return f"{self.prenom} {self.__nom}".strip()

    # ------------------------------------------------- contrat EntiteBase
    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.__nom,
            "prenom": self.prenom,
            "email": self.__email,
            "login": self.__login,
            "role": self.role(),
            "actif": self.actif,
            "derniere_connexion": self.derniere_connexion,
        }

    def valider(self):
        if not self.__login:
            raise ValidationError("login", "obligatoire")
        if not self.__mot_de_passe_hash:
            raise ValidationError("mot de passe", "obligatoire")

    def libelle(self):
        return f"{self.nom_complet()} ({self.role()})"


class Vendeur(Utilisateur):
    """
    Role VENDEUR : consultation du stock et enregistrement des sorties.
    HERITAGE : recupere tout de Utilisateur.
    """

    ROLE = "vendeur"

    def permissions(self):
        # super() = les permissions du parent, puis on ajoute les siennes
        return super().permissions() | {
            "consulter_produits",
            "consulter_stock",
            "consulter_fournisseurs",
            "creer_sortie",
            "consulter_alertes",
        }


class Gestionnaire(Vendeur):
    """
    Role GESTIONNAIRE : gestion complete du catalogue et des mouvements.
    HERITAGE : recupere tout de Vendeur (donc aussi de Utilisateur).
    """

    ROLE = "gestionnaire"

    def permissions(self):
        return super().permissions() | {
            "creer_produit", "modifier_produit", "supprimer_produit",
            "creer_fournisseur", "modifier_fournisseur", "supprimer_fournisseur",
            "creer_entree", "creer_transfert", "creer_ajustement",
            "traiter_alerte", "exporter_rapport",
        }


class Admin(Gestionnaire):
    """
    Role ADMIN : acces total, y compris la gestion des comptes.
    POLYMORPHISME TOTAL : peut() est redefinie pour toujours retourner True.
    """

    ROLE = "admin"

    def permissions(self):
        return super().permissions() | {
            "creer_utilisateur", "modifier_utilisateur", "supprimer_utilisateur",
            "consulter_audit", "administrer_systeme",
        }

    def peut(self, action):
        """L'administrateur est autorise a tout faire."""
        return True


# ---------------------------------------------------------------------
def creer_utilisateur_par_role(role, **kwargs):
    """
    Design Pattern : SIMPLE FACTORY.

    Retourne une instance de la bonne sous-classe en fonction du role
    stocke en base de donnees, sans que l'appelant ait a connaitre
    les classes concretes.
    """
    correspondance = {
        "admin": Admin,
        "gestionnaire": Gestionnaire,
        "vendeur": Vendeur,
    }
    classe = correspondance.get((role or "").lower(), Utilisateur)
    return classe(**kwargs)