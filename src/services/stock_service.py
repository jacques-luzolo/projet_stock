"""Service metier de gestion du stock (orchestration + Observer)."""
from src.exceptions.domain_exceptions import StockInsuffisantError
from src.patterns.factory import MouvementFactory
from src.patterns.observer import (ObservateurAudit, ObservateurJournal,
                                   ObservateurPeremption,
                                   ObservateurSeuilMinimum, SujetObservable)
from src.repositories.mouvement_repository import (AlerteRepository,
                                                   MouvementRepository,
                                                   StockRepository)
from src.repositories.produit_repository import ProduitRepository
from src.utils.logger import logger


class StockService(SujetObservable):
    """
    Coordonne les mouvements, les stocks et les alertes.

    Herite de SujetObservable : chaque operation emet un evenement
    auquel reagissent les observateurs (pattern Observer).
    """

    def __init__(self):
        super().__init__()
        self.depot_produits = ProduitRepository()
        self.depot_mouvements = MouvementRepository()
        self.depot_stocks = StockRepository()
        self.depot_alertes = AlerteRepository()

        # Observateurs branches par defaut
        self.obs_seuil = ObservateurSeuilMinimum()
        self.obs_peremption = ObservateurPeremption()
        self.obs_audit = ObservateurAudit()
        self.attacher(self.obs_seuil)
        self.attacher(self.obs_peremption)
        self.attacher(self.obs_audit)
        self.attacher(ObservateurJournal())

    # ------------------------------------------------------------------
    def enregistrer_mouvement(self, type_mouvement, produit_id, quantite,
                              utilisateur_id, entrepot_source_id=None,
                              entrepot_dest_id=None, prix_unitaire=0,
                              motif=""):
        """
        Cree le mouvement (Factory), l'applique au stock (Polymorphisme),
        le persiste, puis emet un evenement (Observer).
        """
        mouvement = MouvementFactory.creer(
            type_mouvement,
            produit_id=produit_id, quantite=quantite,
            utilisateur_id=utilisateur_id,
            entrepot_source_id=entrepot_source_id,
            entrepot_dest_id=entrepot_dest_id,
            prix_unitaire=prix_unitaire, motif=motif,
        )

        type_maj = mouvement.type_mouvement()

        if type_maj == "ENTREE":
            actuel = self.depot_stocks.quantite(produit_id, entrepot_dest_id)
            self.depot_stocks.definir(produit_id, entrepot_dest_id,
                                      mouvement.appliquer(actuel))

        elif type_maj == "SORTIE":
            actuel = self.depot_stocks.quantite(produit_id, entrepot_source_id)
            self.depot_stocks.definir(produit_id, entrepot_source_id,
                                      mouvement.appliquer(actuel))

        elif type_maj == "TRANSFERT":
            source = self.depot_stocks.quantite(produit_id, entrepot_source_id)
            if quantite > source:
                raise StockInsuffisantError(produit_id, source, quantite)
            dest = self.depot_stocks.quantite(produit_id, entrepot_dest_id)
            self.depot_stocks.definir(produit_id, entrepot_source_id, source - quantite)
            self.depot_stocks.definir(produit_id, entrepot_dest_id, dest + quantite)

        elif type_maj == "AJUSTEMENT":
            cible = entrepot_dest_id or entrepot_source_id
            self.depot_stocks.definir(produit_id, cible, quantite)

        self.depot_mouvements.enregistrer(mouvement)

        # Notification des observateurs
        produit = self.depot_produits.trouver_par_id(produit_id)
        self.emettre("stock_modifie", {
            "produit_id": produit_id,
            "quantite": self.depot_stocks.quantite_totale(produit_id),
            "seuil_min": produit.seuil_min if produit else 0,
            "type_mouvement": type_maj,
        })

        self._persister_alertes()
        return mouvement

    # ------------------------------------------------------------------
    def controler_peremptions(self, jours=30):
        """Parcourt les produits perissables et emet les alertes."""
        produits = self.depot_produits.produits_perissables_proches(jours)
        for p in produits:
            date_p = p.get("date_peremption")
            if not date_p:
                continue
            from datetime import date as _date
            restants = (date_p - _date.today()).days
            self.emettre("controle_peremption",
                         {"produit_id": p["id"], "jours_restants": restants})
        self._persister_alertes()
        return len(produits)

    def _persister_alertes(self):
        """Transfere les alertes en memoire vers la base de donnees."""
        for source in (self.obs_seuil, self.obs_peremption):
            for a in source.alertes:
                self.depot_alertes.creer(a["type_alerte"], a["produit_id"],
                                         a["message"], a["niveau"])
            source.alertes.clear()

    # ------------------------------------------------------------------
    def tableau_de_bord(self):
        """Agrege les indicateurs pour la page Dashboard."""
        stats = self.depot_produits.statistiques()
        stats["alertes"] = self.depot_alertes.compter_actives()
        return stats