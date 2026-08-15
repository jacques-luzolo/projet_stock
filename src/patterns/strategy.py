"""
Design Pattern : STRATEGY (Strategie).

Probleme resolu :
    La valeur d'un stock peut se calculer de plusieurs facons
    (FIFO, LIFO, cout moyen pondere, prix de vente...).
    On veut pouvoir changer de methode sans modifier le code appelant.

Solution :
    Chaque methode de calcul est encapsulee dans une classe qui respecte
    la meme interface. Le contexte recoit la strategie a utiliser et peut
    en changer a tout moment.
"""
from abc import ABC, abstractmethod

from src.utils.logger import logger


class StrategieValorisation(ABC):
    """Interface commune a toutes les methodes de valorisation."""

    NOM = "abstraite"

    @abstractmethod
    def calculer(self, lots):
        """
        Calcule la valeur totale du stock.

        lots : liste de dictionnaires
               [{"quantite": 10, "prix_unitaire": 5.0, "date": ...}, ...]
        """
        raise NotImplementedError

    def libelle(self):
        return self.NOM


class ValorisationFIFO(StrategieValorisation):
    """First In First Out : les lots les plus anciens sortent en premier."""

    NOM = "FIFO (Premier entre, premier sorti)"

    def calculer(self, lots):
        lots_tries = sorted(lots, key=lambda l: l.get("date") or 0)
        return round(sum(l["quantite"] * l["prix_unitaire"] for l in lots_tries), 2)


class ValorisationLIFO(StrategieValorisation):
    """Last In First Out : les lots les plus recents sortent en premier."""

    NOM = "LIFO (Dernier entre, premier sorti)"

    def calculer(self, lots):
        lots_tries = sorted(lots, key=lambda l: l.get("date") or 0, reverse=True)
        return round(sum(l["quantite"] * l["prix_unitaire"] for l in lots_tries), 2)


class ValorisationCoutMoyen(StrategieValorisation):
    """Cout Moyen Pondere : moyenne des prix ponderee par les quantites."""

    NOM = "CMP (Cout moyen pondere)"

    def calculer(self, lots):
        quantite_totale = sum(l["quantite"] for l in lots)
        if quantite_totale == 0:
            return 0.0
        valeur = sum(l["quantite"] * l["prix_unitaire"] for l in lots)
        return round(valeur, 2)

    def cout_unitaire_moyen(self, lots):
        """Prix moyen d'une unite en stock."""
        quantite_totale = sum(l["quantite"] for l in lots)
        if quantite_totale == 0:
            return 0.0
        valeur = sum(l["quantite"] * l["prix_unitaire"] for l in lots)
        return round(valeur / quantite_totale, 2)


class ValorisationPrixVente(StrategieValorisation):
    """Valorisation au prix de vente (valeur commerciale du stock)."""

    NOM = "Prix de vente"

    def calculer(self, lots):
        return round(sum(l["quantite"] * l.get("prix_vente", l["prix_unitaire"])
                         for l in lots), 2)


class ContexteValorisation:
    """
    Contexte utilisant une strategie interchangeable.

    Exemple :
        ctx = ContexteValorisation(ValorisationFIFO())
        valeur = ctx.evaluer(lots)

        ctx.changer_strategie(ValorisationCoutMoyen())
        autre_valeur = ctx.evaluer(lots)
    """

    def __init__(self, strategie=None):
        self._strategie = strategie or ValorisationCoutMoyen()

    @property
    def strategie(self):
        return self._strategie

    def changer_strategie(self, strategie):
        """Remplace la strategie a chaud."""
        self._strategie = strategie
        logger.info("Strategie de valorisation : %s", strategie.libelle())

    def evaluer(self, lots):
        """Le code appelant ne change jamais, seule la strategie varie."""
        return self._strategie.calculer(lots)

    @staticmethod
    def strategies_disponibles():
        """Dictionnaire libelle -> instance (pour un menu Streamlit)."""
        return {
            ValorisationFIFO.NOM: ValorisationFIFO(),
            ValorisationLIFO.NOM: ValorisationLIFO(),
            ValorisationCoutMoyen.NOM: ValorisationCoutMoyen(),
            ValorisationPrixVente.NOM: ValorisationPrixVente(),
        }