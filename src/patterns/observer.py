"""
Design Pattern : OBSERVER (Observateur).

Probleme resolu :
    Quand le stock d'un produit change, plusieurs actions doivent se
    declencher (creer une alerte, journaliser, tracer dans l'audit...).
    On ne veut pas que le service de stock connaisse tous ces destinataires.

Solution :
    Le "sujet observable" tient une liste d'observateurs et les previent
    tous lorsqu'un evenement survient. On peut ajouter ou retirer un
    observateur sans modifier une seule ligne du service de stock.
"""
from abc import ABC, abstractmethod
from datetime import datetime

from src.utils.logger import logger


class Observateur(ABC):
    """Interface commune a tous les observateurs."""

    @abstractmethod
    def notifier(self, evenement, donnees):
        """Reagit a un evenement emis par le sujet observe."""
        raise NotImplementedError


class SujetObservable:
    """Objet capable de prevenir une liste d'observateurs."""

    def __init__(self):
        self._observateurs = []

    def attacher(self, observateur):
        """Abonne un observateur aux evenements."""
        if observateur not in self._observateurs:
            self._observateurs.append(observateur)
            logger.debug("Observateur attache : %s", type(observateur).__name__)

    def detacher(self, observateur):
        """Desabonne un observateur."""
        if observateur in self._observateurs:
            self._observateurs.remove(observateur)

    def emettre(self, evenement, donnees):
        """Previent tous les observateurs attaches."""
        for obs in list(self._observateurs):
            try:
                obs.notifier(evenement, donnees)
            except Exception as err:
                # Un observateur defaillant ne doit pas bloquer les autres
                logger.error("Observateur %s en echec : %s",
                             type(obs).__name__, err)

    @property
    def nb_observateurs(self):
        return len(self._observateurs)


# ---------------------------------------------------------------------
# Observateurs concrets
# ---------------------------------------------------------------------
class ObservateurSeuilMinimum(Observateur):
    """Cree une alerte lorsque le stock passe sous le seuil minimum."""

    def __init__(self):
        self.alertes = []

    def notifier(self, evenement, donnees):
        if evenement != "stock_modifie":
            return

        quantite = donnees.get("quantite", 0)
        seuil = donnees.get("seuil_min", 0)

        if quantite <= seuil:
            niveau = "CRITIQUE" if quantite == 0 else "WARNING"
            self.alertes.append({
                "type_alerte": "SEUIL_MIN",
                "produit_id": donnees.get("produit_id"),
                "message": f"Stock bas : {quantite} unite(s) (seuil {seuil})",
                "niveau": niveau,
                "horodatage": datetime.now(),
            })
            logger.warning("ALERTE SEUIL - produit %s : %s <= %s",
                           donnees.get("produit_id"), quantite, seuil)


class ObservateurPeremption(Observateur):
    """Cree une alerte pour les produits perimes ou proches de l'etre."""

    def __init__(self, seuil_jours=30):
        self.seuil_jours = seuil_jours
        self.alertes = []

    def notifier(self, evenement, donnees):
        if evenement != "controle_peremption":
            return

        jours = donnees.get("jours_restants")
        if jours is None:
            return

        if jours < 0:
            message = f"Produit perime depuis {abs(jours)} jour(s)"
            niveau = "CRITIQUE"
        elif jours <= self.seuil_jours:
            message = f"Peremption dans {jours} jour(s)"
            niveau = "WARNING"
        else:
            return

        self.alertes.append({
            "type_alerte": "PEREMPTION",
            "produit_id": donnees.get("produit_id"),
            "message": message,
            "niveau": niveau,
            "horodatage": datetime.now(),
        })
        logger.warning("ALERTE PEREMPTION - produit %s : %s",
                       donnees.get("produit_id"), message)


class ObservateurJournal(Observateur):
    """Journalise tous les evenements dans le fichier de logs."""

    def notifier(self, evenement, donnees):
        logger.info("Evenement '%s' : %s", evenement, donnees)


class ObservateurAudit(Observateur):
    """Conserve un historique en memoire (affichable dans l'interface)."""

    def __init__(self, taille_max=200):
        self.historique = []
        self.taille_max = taille_max

    def notifier(self, evenement, donnees):
        self.historique.append({
            "evenement": evenement,
            "donnees": donnees,
            "horodatage": datetime.now(),
        })
        if len(self.historique) > self.taille_max:
            self.historique.pop(0)

    def derniers(self, n=10):
        """Retourne les n derniers evenements enregistres."""
        return self.historique[-n:]