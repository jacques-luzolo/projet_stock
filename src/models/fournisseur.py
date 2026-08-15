"""
Modele metier Fournisseur.

Concepts POO demontres :
- HERITAGE      : Fournisseur herite de EntiteBase
- ENCAPSULATION : raison_sociale, email et telephone sont prives et valides
"""
from src.exceptions.domain_exceptions import ValidationError
from src.models.base import EntiteBase
from src.utils.security import valider_email


class Fournisseur(EntiteBase):
    """Partenaire commercial qui approvisionne les produits."""

    def __init__(self, raison_sociale, contact="", telephone="", email="",
                 adresse="", ville="", pays="RDC", actif=True,
                 id_=None, cree_le=None):
        super().__init__(id_, cree_le)

        # Attributs prives
        self.__raison_sociale = ""
        self.__email = ""
        self.__telephone = ""

        # Affectation via les setters (validation automatique)
        self.raison_sociale = raison_sociale
        self.telephone = telephone
        self.email = email

        # Attributs publics
        self.contact = contact
        self.adresse = adresse
        self.ville = ville
        self.pays = pays
        self.actif = actif

    # -------------------------------------------------- raison sociale
    @property
    def raison_sociale(self):
        return self.__raison_sociale

    @raison_sociale.setter
    def raison_sociale(self, valeur):
        valeur = (valeur or "").strip()
        if len(valeur) < 2:
            raise ValidationError("raison sociale", "2 caracteres minimum")
        self.__raison_sociale = valeur

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

    # -------------------------------------------------------- telephone
    @property
    def telephone(self):
        return self.__telephone

    @telephone.setter
    def telephone(self, valeur):
        valeur = (valeur or "").strip()
        if valeur and len(valeur) < 8:
            raise ValidationError("telephone", "8 caracteres minimum")
        self.__telephone = valeur

    # ---------------------------------------------------- infos metier
    def coordonnees(self):
        """Retourne une chaine lisible avec les coordonnees du fournisseur."""
        elements = [e for e in (self.__telephone, self.__email, self.ville) if e]
        return " | ".join(elements) if elements else "Aucune coordonnee"

    def est_joignable(self):
        """True si au moins un moyen de contact est renseigne."""
        return bool(self.__telephone or self.__email)

    # ------------------------------------------------ contrat EntiteBase
    def to_dict(self):
        return {
            "id": self.id,
            "raison_sociale": self.__raison_sociale,
            "contact": self.contact,
            "telephone": self.__telephone,
            "email": self.__email,
            "adresse": self.adresse,
            "ville": self.ville,
            "pays": self.pays,
            "actif": self.actif,
        }

    def valider(self):
        if not self.__raison_sociale:
            raise ValidationError("raison sociale", "obligatoire")
        if not self.est_joignable():
            raise ValidationError("contact", "telephone ou email obligatoire")

    def libelle(self):
        return self.__raison_sociale