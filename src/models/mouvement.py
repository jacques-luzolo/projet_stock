"""
Modeles des mouvements de stock.

Concepts POO demontres :
- ABSTRACTION   : Mouvement est une classe abstraite (ABC).
                  Elle impose aux classes filles d'implementer appliquer()
                  et sens(), mais ne peut pas etre instanciee elle-meme.
- HERITAGE      : Entree / Sortie / Transfert / Ajustement heritent de Mouvement.
- POLYMORPHISME : appliquer(stock) donne un resultat different selon le type
                  de mouvement, alors que le code appelant est identique.
"""
from abc import abstractmethod
from datetime import datetime

from src.exceptions.domain_exceptions import (
    QuantiteInvalideError,
    StockInsuffisantError,
    ValidationError,
)
from src.models.base import EntiteBase


class Mouvement(EntiteBase):
    """
    Operation qui modifie le stock (CLASSE ABSTRAITE).

    On ne peut pas ecrire Mouvement(...) directement :
    il faut utiliser Entree, Sortie, Transfert ou Ajustement.
    """

    TYPE = "ABSTRAIT"

    def __init__(self, produit_id, quantite, utilisateur_id,
                 entrepot_source_id=None, entrepot_dest_id=None,
                 prix_unitaire=0.0, motif="", date_mouvement=None, id_=None):
        super().__init__(id_, date_mouvement)

        self.__quantite = 0

        self.produit_id = produit_id
        self.quantite = quantite          # passe par le setter (validation)
        self.utilisateur_id = utilisateur_id
        self.entrepot_source_id = entrepot_source_id
        self.entrepot_dest_id = entrepot_dest_id
        self.prix_unitaire = float(prix_unitaire or 0)
        self.motif = motif
        self.date_mouvement = date_mouvement or datetime.now()

    # --------------------------------------------------- ENCAPSULATION
    @property
    def quantite(self):
        return self.__quantite

    @quantite.setter
    def quantite(self, valeur):
        try:
            valeur = int(valeur)
        except (TypeError, ValueError):
            raise QuantiteInvalideError(valeur)
        if valeur <= 0:
            raise QuantiteInvalideError(valeur)
        self.__quantite = valeur

    # ------------------------------------------- METHODES ABSTRAITES
    @abstractmethod
    def appliquer(self, stock_actuel):
        """
        Calcule le nouveau stock apres application du mouvement.
        Chaque sous-classe l'implemente a sa maniere (POLYMORPHISME).
        """
        raise NotImplementedError

    @abstractmethod
    def sens(self):
        """+1 si le stock augmente, -1 s'il diminue, 0 s'il est inchange."""
        raise NotImplementedError

    # -------------------------------------------------- calculs metier
    def montant_total(self):
        """Valeur monetaire du mouvement."""
        return round(self.__quantite * self.prix_unitaire, 2)

    def type_mouvement(self):
        return self.TYPE

    # ------------------------------------------------ contrat EntiteBase
    def to_dict(self):
        return {
            "id": self.id,
            "type_mouvement": self.TYPE,
            "produit_id": self.produit_id,
            "quantite": self.__quantite,
            "entrepot_source_id": self.entrepot_source_id,
            "entrepot_dest_id": self.entrepot_dest_id,
            "prix_unitaire": self.prix_unitaire,
            "motif": self.motif,
            "utilisateur_id": self.utilisateur_id,
            "date_mouvement": self.date_mouvement,
            "montant_total": self.montant_total(),
        }

    def valider(self):
        if not self.produit_id:
            raise ValidationError("produit", "obligatoire")
        if not self.utilisateur_id:
            raise ValidationError("utilisateur", "obligatoire")

    def libelle(self):
        return f"{self.TYPE} x{self.__quantite}"


class Entree(Mouvement):
    """Reception de marchandise : le stock AUGMENTE."""

    TYPE = "ENTREE"

    def sens(self):
        return +1

    def appliquer(self, stock_actuel):
        return stock_actuel + self.quantite

    def valider(self):
        super().valider()
        if not self.entrepot_dest_id:
            raise ValidationError("entrepot destination",
                                  "obligatoire pour une entree")


class Sortie(Mouvement):
    """Vente ou consommation : le stock DIMINUE."""

    TYPE = "SORTIE"

    def sens(self):
        return -1

    def appliquer(self, stock_actuel):
        if self.quantite > stock_actuel:
            raise StockInsuffisantError(self.produit_id, stock_actuel, self.quantite)
        return stock_actuel - self.quantite

    def valider(self):
        super().valider()
        if not self.entrepot_source_id:
            raise ValidationError("entrepot source",
                                  "obligatoire pour une sortie")


class Transfert(Mouvement):
    """Deplacement entre deux entrepots : le stock GLOBAL ne change pas."""

    TYPE = "TRANSFERT"

    def sens(self):
        return 0

    def appliquer(self, stock_actuel):
        if self.quantite > stock_actuel:
            raise StockInsuffisantError(self.produit_id, stock_actuel, self.quantite)
        return stock_actuel     # le total reste identique

    def valider(self):
        super().valider()
        if not self.entrepot_source_id or not self.entrepot_dest_id:
            raise ValidationError("entrepots",
                                  "source et destination obligatoires")
        if self.entrepot_source_id == self.entrepot_dest_id:
            raise ValidationError("entrepots",
                                  "source et destination doivent etre differents")


class Ajustement(Mouvement):
    """Correction d'inventaire : le stock DEVIENT la quantite indiquee."""

    TYPE = "AJUSTEMENT"

    def sens(self):
        return 0

    def appliquer(self, stock_actuel):
        return self.quantite    # remplacement direct de la valeur

    def ecart(self, stock_actuel):
        """Difference entre le stock theorique et le stock reel."""
        return self.quantite - stock_actuel

    def valider(self):
        super().valider()
        if not self.motif:
            raise ValidationError("motif",
                                  "obligatoire pour justifier un ajustement")