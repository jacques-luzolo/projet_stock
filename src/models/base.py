"""
Classe de base abstraite de toutes les entites du domaine.

Concept POO : ABSTRACTION
- ABC : cette classe ne peut pas etre instanciee directement
- @abstractmethod : les classes filles DOIVENT implementer ces methodes
"""
from abc import ABC, abstractmethod
from datetime import datetime


class EntiteBase(ABC):
    """Contrat commun a toutes les entites de l'application."""

    def __init__(self, id_=None, cree_le=None):
        self._id = id_
        self._cree_le = cree_le or datetime.now()

    @property
    def id(self):
        """Identifiant technique (encapsule)."""
        return self._id

    @id.setter
    def id(self, valeur):
        if valeur is not None and (not isinstance(valeur, int) or valeur <= 0):
            raise ValueError("L'identifiant doit etre un entier positif.")
        self._id = valeur

    @property
    def cree_le(self):
        return self._cree_le

    @abstractmethod
    def to_dict(self):
        """Convertit l'entite en dictionnaire."""
        raise NotImplementedError

    @abstractmethod
    def valider(self):
        """Verifie que les donnees sont coherentes."""
        raise NotImplementedError

    @abstractmethod
    def libelle(self):
        """Texte court affichable a l'ecran."""
        raise NotImplementedError

    def est_persiste(self):
        """True si l'entite existe deja en base de donnees."""
        return self._id is not None

    def __eq__(self, autre):
        if not isinstance(autre, EntiteBase):
            return NotImplemented
        return type(self) is type(autre) and self._id == autre._id

    def __hash__(self):
        return hash((type(self).__name__, self._id))

    def __repr__(self):
        return f"<{type(self).__name__} id={self._id} {self.libelle()}>"