"""
Modeles metier lies aux produits.

Concepts POO demontres :
- ENCAPSULATION : attributs prives (__prix_achat) exposes via @property/@setter
                  qui valident les valeurs (impossible de mettre un prix negatif)
- HERITAGE      : Produit -> ProduitPerissable
- POLYMORPHISME : est_alerte(), type_produit(), libelle() redefinies
"""
from datetime import date, datetime

from src.exceptions.domain_exceptions import ValidationError
from src.models.base import EntiteBase


class Categorie(EntiteBase):
    """Categorie de classement des produits."""

    def __init__(self, nom, description="", id_=None, parent_id=None):
        super().__init__(id_)
        self.__nom = ""
        self.nom = nom
        self.description = description
        self.parent_id = parent_id

    @property
    def nom(self):
        return self.__nom

    @nom.setter
    def nom(self, valeur):
        valeur = (valeur or "").strip()
        if len(valeur) < 2:
            raise ValidationError("nom categorie", "2 caracteres minimum")
        self.__nom = valeur

    def to_dict(self):
        return {"id": self.id, "nom": self.__nom,
                "description": self.description, "parent_id": self.parent_id}

    def valider(self):
        if not self.__nom:
            raise ValidationError("nom categorie", "obligatoire")

    def libelle(self):
        return self.__nom


class Produit(EntiteBase):
    """
    Produit standard du stock.

    ENCAPSULATION : les attributs sensibles sont prives (double underscore)
    et accessibles uniquement via des proprietes qui valident les valeurs.
    """

    def __init__(self, reference, designation, prix_achat=0.0, prix_vente=0.0,
                 seuil_min=0, seuil_max=0, unite="pcs", categorie_id=None,
                 fournisseur_id=None, description="", actif=True,
                 id_=None, cree_le=None):
        super().__init__(id_, cree_le)

        # Attributs prives
        self.__reference = ""
        self.__designation = ""
        self.__prix_achat = 0.0
        self.__prix_vente = 0.0
        self.__seuil_min = 0
        self.__seuil_max = 0

        # Affectation via les setters (donc validation automatique)
        self.reference = reference
        self.designation = designation
        self.prix_achat = prix_achat
        self.prix_vente = prix_vente
        self.seuil_min = seuil_min
        self.seuil_max = seuil_max

        # Attributs publics simples
        self.unite = unite
        self.categorie_id = categorie_id
        self.fournisseur_id = fournisseur_id
        self.description = description
        self.actif = actif
        self._quantite_totale = 0

    # ------------------------------------------------------- reference
    @property
    def reference(self):
        return self.__reference

    @reference.setter
    def reference(self, valeur):
        valeur = (valeur or "").strip().upper()
        if len(valeur) < 3:
            raise ValidationError("reference", "3 caracteres minimum")
        self.__reference = valeur

    # ------------------------------------------------------ designation
    @property
    def designation(self):
        return self.__designation

    @designation.setter
    def designation(self, valeur):
        valeur = (valeur or "").strip()
        if len(valeur) < 2:
            raise ValidationError("designation", "2 caracteres minimum")
        self.__designation = valeur

    # ------------------------------------------------------- prix achat
    @property
    def prix_achat(self):
        return self.__prix_achat

    @prix_achat.setter
    def prix_achat(self, valeur):
        valeur = float(valeur or 0)
        if valeur < 0:
            raise ValidationError("prix achat", "ne peut pas etre negatif")
        self.__prix_achat = round(valeur, 2)

    # ------------------------------------------------------- prix vente
    @property
    def prix_vente(self):
        return self.__prix_vente

    @prix_vente.setter
    def prix_vente(self, valeur):
        valeur = float(valeur or 0)
        if valeur < 0:
            raise ValidationError("prix vente", "ne peut pas etre negatif")
        self.__prix_vente = round(valeur, 2)

    # ------------------------------------------------------------ seuils
    @property
    def seuil_min(self):
        return self.__seuil_min

    @seuil_min.setter
    def seuil_min(self, valeur):
        valeur = int(valeur or 0)
        if valeur < 0:
            raise ValidationError("seuil minimum", "ne peut pas etre negatif")
        self.__seuil_min = valeur

    @property
    def seuil_max(self):
        return self.__seuil_max

    @seuil_max.setter
    def seuil_max(self, valeur):
        valeur = int(valeur or 0)
        if valeur and valeur < self.__seuil_min:
            raise ValidationError("seuil maximum", "doit etre superieur au seuil minimum")
        self.__seuil_max = valeur

    # ---------------------------------------------------------- quantite
    @property
    def quantite_totale(self):
        return self._quantite_totale

    @quantite_totale.setter
    def quantite_totale(self, valeur):
        self._quantite_totale = max(0, int(valeur or 0))

    # ---------------------------------------------------- calculs metier
    def marge_unitaire(self):
        """Benefice realise sur une unite vendue."""
        return round(self.__prix_vente - self.__prix_achat, 2)

    def taux_marge(self):
        """Marge exprimee en pourcentage du prix d'achat."""
        if self.__prix_achat == 0:
            return 0.0
        return round(self.marge_unitaire() / self.__prix_achat * 100, 2)

    def valeur_stock(self):
        """Valeur immobilisee en stock (au prix d'achat)."""
        return round(self._quantite_totale * self.__prix_achat, 2)

    def est_sous_seuil(self):
        """True si la quantite est inferieure ou egale au seuil minimum."""
        return self._quantite_totale <= self.__seuil_min

    def est_alerte(self):
        """POLYMORPHISME : redefinie dans ProduitPerissable."""
        return self.est_sous_seuil()

    def type_produit(self):
        return "STANDARD"

    # -------------------------------------------------- contrat EntiteBase
    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.__reference,
            "designation": self.__designation,
            "description": self.description,
            "categorie_id": self.categorie_id,
            "fournisseur_id": self.fournisseur_id,
            "unite": self.unite,
            "prix_achat": self.__prix_achat,
            "prix_vente": self.__prix_vente,
            "seuil_min": self.__seuil_min,
            "seuil_max": self.__seuil_max,
            "perissable": False,
            "date_peremption": None,
            "actif": self.actif,
            "quantite_totale": self._quantite_totale,
            "type": self.type_produit(),
        }

    def valider(self):
        if not self.__reference:
            raise ValidationError("reference", "obligatoire")
        if not self.__designation:
            raise ValidationError("designation", "obligatoire")
        if self.__prix_vente < self.__prix_achat:
            raise ValidationError("prix vente", "doit etre superieur au prix d'achat")

    def libelle(self):
        return f"{self.__reference} - {self.__designation}"


class ProduitPerissable(Produit):
    """
    Produit possedant une date de peremption.

    HERITAGE      : recupere tout le comportement de Produit
    POLYMORPHISME : est_alerte(), type_produit(), to_dict(), libelle() redefinies
    """

    SEUIL_ALERTE_JOURS = 30

    def __init__(self, reference, designation, date_peremption=None, **kwargs):
        super().__init__(reference, designation, **kwargs)
        self.__date_peremption = None
        self.date_peremption = date_peremption

    @property
    def date_peremption(self):
        return self.__date_peremption

    @date_peremption.setter
    def date_peremption(self, valeur):
        if isinstance(valeur, str) and valeur:
            valeur = datetime.strptime(valeur, "%Y-%m-%d").date()
        if isinstance(valeur, datetime):
            valeur = valeur.date()
        self.__date_peremption = valeur

    def jours_avant_peremption(self):
        """Nombre de jours restants (negatif si deja perime)."""
        if self.__date_peremption is None:
            return None
        return (self.__date_peremption - date.today()).days

    def est_perime(self):
        jours = self.jours_avant_peremption()
        return jours is not None and jours < 0

    def bientot_perime(self):
        jours = self.jours_avant_peremption()
        return jours is not None and 0 <= jours <= self.SEUIL_ALERTE_JOURS

    # ------------------------------------------------------ POLYMORPHISME
    def est_alerte(self):
        """Alerte si stock bas OU peremption proche/depassee."""
        return super().est_alerte() or self.est_perime() or self.bientot_perime()

    def type_produit(self):
        return "PERISSABLE"

    def to_dict(self):
        donnees = super().to_dict()
        donnees.update({
            "perissable": True,
            "date_peremption": self.__date_peremption,
            "jours_restants": self.jours_avant_peremption(),
            "type": self.type_produit(),
        })
        return donnees

    def valider(self):
        super().valider()
        if self.__date_peremption is None:
            raise ValidationError("date de peremption",
                                  "obligatoire pour un produit perissable")

    def libelle(self):
        suffixe = ""
        if self.est_perime():
            suffixe = " [PERIME]"
        elif self.bientot_perime():
            suffixe = f" [J-{self.jours_avant_peremption()}]"
        return super().libelle() + suffixe