"""
Demonstration des Design Patterns du projet StockManager.

A executer avec :  python scripts/demo_patterns.py
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.connection import DatabaseConnection
from src.exceptions.domain_exceptions import ValidationError
from src.patterns.factory import MouvementFactory, ProduitFactory
from src.patterns.observer import (ObservateurAudit, ObservateurJournal,
                                   ObservateurPeremption,
                                   ObservateurSeuilMinimum, SujetObservable)
from src.patterns.strategy import (ContexteValorisation, ValorisationCoutMoyen,
                                   ValorisationFIFO, ValorisationLIFO,
                                   ValorisationPrixVente)


def titre(texte):
    print("\n" + "=" * 70)
    print(f"  {texte}")
    print("=" * 70)


# =====================================================================
def demo_singleton():
    titre("PATTERN 1 : SINGLETON - une seule instance du pool de connexions")

    a = DatabaseConnection()
    b = DatabaseConnection()
    c = DatabaseConnection()

    print(f"  Adresse memoire instance A : {id(a)}")
    print(f"  Adresse memoire instance B : {id(b)}")
    print(f"  Adresse memoire instance C : {id(c)}")
    print(f"\n  a is b is c  ->  {a is b is c}")
    print("  --> Malgre 3 appels a DatabaseConnection(), un SEUL objet existe.")
    print("      Economie de ressources : un seul pool de connexions BD.")


# =====================================================================
def demo_factory():
    titre("PATTERN 2 : FACTORY METHOD - creer sans connaitre les classes")

    print(f"  Types geres par la fabrique : {MouvementFactory.types_disponibles()}\n")

    demandes = [
        ("ENTREE", {"produit_id": 1, "quantite": 50, "utilisateur_id": 1,
                    "entrepot_dest_id": 1, "prix_unitaire": 12.5}),
        ("SORTIE", {"produit_id": 1, "quantite": 20, "utilisateur_id": 1,
                    "entrepot_source_id": 1, "prix_unitaire": 20.0}),
        ("TRANSFERT", {"produit_id": 1, "quantite": 10, "utilisateur_id": 1,
                       "entrepot_source_id": 1, "entrepot_dest_id": 2}),
        ("AJUSTEMENT", {"produit_id": 1, "quantite": 95, "utilisateur_id": 1,
                        "motif": "Inventaire trimestriel"}),
    ]

    print(f"  {'DEMANDE':<12} {'CLASSE INSTANCIEE':<18} {'SENS':>5} {'MONTANT':>10}")
    print("  " + "-" * 50)
    for type_demande, params in demandes:
        mvt = MouvementFactory.creer(type_demande, **params)
        print(f"  {type_demande:<12} {type(mvt).__name__:<18} "
              f"{mvt.sens():>+5} {mvt.montant_total():>10.2f}")

    print("\n  --> Demande d'un type inexistant :")
    try:
        MouvementFactory.creer("TELEPORTATION", produit_id=1,
                               quantite=1, utilisateur_id=1)
    except ValidationError as e:
        print(f"      REFUSE : {e}")

    print("\n  ProduitFactory - choix automatique de la classe concrete :")
    exemples = [
        {"reference": "INF-010", "designation": "Ecran 24 pouces",
         "perissable": False, "prix_achat": 120, "prix_vente": 180},
        {"reference": "ALI-010", "designation": "Fromage frais",
         "perissable": True, "date_peremption": "2026-11-30",
         "prix_achat": 3, "prix_vente": 5},
    ]
    for donnees in exemples:
        p = ProduitFactory.creer(donnees)
        print(f"    {p.reference:<10} -> {type(p).__name__:<18} "
              f"({p.type_produit()})")


# =====================================================================
def demo_observer():
    titre("PATTERN 3 : OBSERVER - alertes declenchees automatiquement")

    service = SujetObservable()

    obs_seuil = ObservateurSeuilMinimum()
    obs_perem = ObservateurPeremption(seuil_jours=30)
    obs_audit = ObservateurAudit()

    service.attacher(obs_seuil)
    service.attacher(obs_perem)
    service.attacher(ObservateurJournal())
    service.attacher(obs_audit)

    print(f"  Observateurs abonnes : {service.nb_observateurs}\n")

    print("  [Evt 1] Sortie de stock -> il reste 3 unites (seuil = 20)")
    service.emettre("stock_modifie",
                    {"produit_id": 2, "quantite": 3, "seuil_min": 20})

    print("  [Evt 2] Stock epuise -> 0 unite (seuil = 10)")
    service.emettre("stock_modifie",
                    {"produit_id": 5, "quantite": 0, "seuil_min": 10})

    print("  [Evt 3] Controle peremption -> perime depuis 4 jours")
    service.emettre("controle_peremption",
                    {"produit_id": 7, "jours_restants": -4})

    print("  [Evt 4] Controle peremption -> expire dans 9 jours")
    service.emettre("controle_peremption",
                    {"produit_id": 8, "jours_restants": 9})

    print(f"\n  Alertes SEUIL generees      : {len(obs_seuil.alertes)}")
    for a in obs_seuil.alertes:
        print(f"    [{a['niveau']:<8}] produit {a['produit_id']} : {a['message']}")

    print(f"\n  Alertes PEREMPTION generees : {len(obs_perem.alertes)}")
    for a in obs_perem.alertes:
        print(f"    [{a['niveau']:<8}] produit {a['produit_id']} : {a['message']}")

    print(f"\n  Journal d'audit : {len(obs_audit.historique)} evenements traces")
    print("\n  --> Le service de stock n'a AUCUNE ligne de code d'alerte :")
    print("      il se contente d'appeler emettre(). Les observateurs reagissent.")


# =====================================================================
def demo_strategy():
    titre("PATTERN 4 : STRATEGY - valorisation du stock interchangeable")

    maintenant = datetime.now()
    lots = [
        {"quantite": 50, "prix_unitaire": 10.00, "prix_vente": 15.00,
         "date": maintenant - timedelta(days=90)},
        {"quantite": 30, "prix_unitaire": 12.00, "prix_vente": 18.00,
         "date": maintenant - timedelta(days=45)},
        {"quantite": 20, "prix_unitaire": 15.00, "prix_vente": 22.00,
         "date": maintenant - timedelta(days=5)},
    ]

    total = sum(l["quantite"] for l in lots)
    print(f"  Stock analyse : {total} unites reparties en {len(lots)} lots\n")
    print(f"  {'LOT':<6} {'QTE':>5} {'PU ACHAT':>10} {'PU VENTE':>10} {'AGE':>8}")
    print("  " + "-" * 44)
    for i, l in enumerate(lots, 1):
        age = (maintenant - l["date"]).days
        print(f"  #{i:<5} {l['quantite']:>5} {l['prix_unitaire']:>10.2f} "
              f"{l['prix_vente']:>10.2f} {age:>6} j")

    contexte = ContexteValorisation()

    print(f"\n  {'STRATEGIE APPLIQUEE':<40} {'VALEUR (USD)':>14}")
    print("  " + "-" * 56)
    for strategie in (ValorisationFIFO(), ValorisationLIFO(),
                      ValorisationCoutMoyen(), ValorisationPrixVente()):
        contexte.changer_strategie(strategie)
        print(f"  {strategie.libelle():<40} {contexte.evaluer(lots):>14.2f}")

    cmp_strategie = ValorisationCoutMoyen()
    print(f"\n  Cout unitaire moyen pondere : "
          f"{cmp_strategie.cout_unitaire_moyen(lots):.2f} USD/unite")

    print("\n  --> Le code appelant est TOUJOURS  contexte.evaluer(lots)")
    print("      Seule la strategie injectee change le resultat.")


# =====================================================================
if __name__ == "__main__":
    print("\n" + "#" * 70)
    print("#  StockManager - DEMONSTRATION DES DESIGN PATTERNS")
    print("#" * 70)

    demo_singleton()
    demo_factory()
    demo_observer()
    demo_strategy()

    print("\n" + "=" * 70)
    print("  4 PATTERNS DEMONTRES :")
    print("    1. Singleton      -> src/database/connection.py")
    print("    2. Factory Method -> src/patterns/factory.py")
    print("    3. Observer       -> src/patterns/observer.py")
    print("    4. Strategy       -> src/patterns/strategy.py")
    print("    5. Repository/DAO -> src/repositories/  (couche d'acces BD)")
    print("=" * 70 + "\n")