"""
Script de demonstration des concepts POO du projet StockManager.

A executer avec :  python scripts/demo_poo.py

Ce script prouve, exemple a l'appui, les 4 piliers de la POO :
  1. ENCAPSULATION
  2. HERITAGE
  3. POLYMORPHISME
  4. ABSTRACTION
"""
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.exceptions.domain_exceptions import (
    QuantiteInvalideError,
    StockInsuffisantError,
    ValidationError,
)
from src.models.mouvement import Ajustement, Entree, Mouvement, Sortie, Transfert
from src.models.produit import Produit, ProduitPerissable
from src.models.utilisateur import Admin, Gestionnaire, Utilisateur, Vendeur


def titre(texte):
    print("\n" + "=" * 68)
    print(f"  {texte}")
    print("=" * 68)


# =====================================================================
# 1. ENCAPSULATION
# =====================================================================
def demo_encapsulation():
    titre("1. ENCAPSULATION - les donnees sont protegees")

    p = Produit("INF-001", "Ordinateur portable HP",
                prix_achat=850, prix_vente=1050, seuil_min=5)

    print(f"  Produit cree      : {p.libelle()}")
    print(f"  Prix d'achat      : {p.prix_achat} USD   (lu via @property)")
    print(f"  Marge unitaire    : {p.marge_unitaire()} USD")
    print(f"  Taux de marge     : {p.taux_marge()} %")

    print("\n  --> Tentative d'acces direct a l'attribut prive :")
    try:
        print(p.__prix_achat)
    except AttributeError:
        print("      AttributeError : __prix_achat est inaccessible de l'exterieur")

    print("\n  --> Tentative d'affectation d'un prix negatif :")
    try:
        p.prix_achat = -100
    except ValidationError as e:
        print(f"      REFUSE : {e}")

    print("\n  --> Affectation d'une valeur valide :")
    p.prix_achat = 900
    print(f"      Nouveau prix d'achat : {p.prix_achat} USD")
    print(f"      Nouvelle marge       : {p.marge_unitaire()} USD")


# =====================================================================
# 2. HERITAGE
# =====================================================================
def demo_heritage():
    titre("2. HERITAGE - ProduitPerissable herite de Produit")

    lait = ProduitPerissable(
        "ALI-001", "Lait UHT 1L",
        date_peremption=date.today() + timedelta(days=12),
        prix_achat=1.20, prix_vente=2.00, seuil_min=100,
    )
    lait.quantite_totale = 250

    print(f"  Objet             : {lait.libelle()}")
    print(f"  Classe            : {type(lait).__name__}")
    print(f"  Chaine d'heritage : "
          f"{' -> '.join(c.__name__ for c in type(lait).__mro__[:4])}")

    print("\n  Methodes HERITEES de Produit :")
    print(f"    marge_unitaire()      = {lait.marge_unitaire()} USD")
    print(f"    valeur_stock()        = {lait.valeur_stock()} USD")
    print(f"    est_sous_seuil()      = {lait.est_sous_seuil()}")

    print("\n  Methodes PROPRES a ProduitPerissable :")
    print(f"    jours_avant_peremption() = {lait.jours_avant_peremption()} jours")
    print(f"    bientot_perime()         = {lait.bientot_perime()}")
    print(f"    est_perime()             = {lait.est_perime()}")

    print(f"\n  isinstance(lait, Produit) = {isinstance(lait, Produit)}")


# =====================================================================
# 3. POLYMORPHISME
# =====================================================================
def demo_polymorphisme_produits():
    titre("3a. POLYMORPHISME - est_alerte() selon le type de produit")

    standard = Produit("INF-002", "Souris sans fil",
                       prix_achat=12, prix_vente=20, seuil_min=20)
    standard.quantite_totale = 251           # stock OK

    perissable = ProduitPerissable(
        "ALI-002", "Yaourt nature",
        date_peremption=date.today() + timedelta(days=5),
        prix_achat=0.5, prix_vente=1.0, seuil_min=10,
    )
    perissable.quantite_totale = 500         # stock OK mais peremption proche

    print(f"  {'PRODUIT':<28} {'TYPE':<12} {'STOCK':>6}  ALERTE ?")
    print("  " + "-" * 60)
    for p in (standard, perissable):
        print(f"  {p.libelle():<28} {p.type_produit():<12} "
              f"{p.quantite_totale:>6}  {p.est_alerte()}")

    print("\n  --> Meme appel  p.est_alerte()  mais logique differente :")
    print("      Produit           : uniquement le seuil de stock")
    print("      ProduitPerissable : seuil de stock OU date de peremption")


def demo_polymorphisme_mouvements():
    titre("3b. POLYMORPHISME - appliquer() selon le type de mouvement")

    stock_depart = 100
    print(f"  Stock initial : {stock_depart} unites\n")

    mouvements = [
        Entree(produit_id=1, quantite=20, utilisateur_id=1, entrepot_dest_id=1),
        Sortie(produit_id=1, quantite=20, utilisateur_id=1, entrepot_source_id=1),
        Transfert(produit_id=1, quantite=20, utilisateur_id=1,
                  entrepot_source_id=1, entrepot_dest_id=2),
        Ajustement(produit_id=1, quantite=20, utilisateur_id=1,
                   motif="Inventaire annuel"),
    ]

    print(f"  {'TYPE':<14} {'SENS':>5}   {'CALCUL':<22} {'NOUVEAU STOCK':>13}")
    print("  " + "-" * 60)
    for m in mouvements:
        nouveau = m.appliquer(stock_depart)
        signe = {1: "+1", -1: "-1", 0: " 0"}[m.sens()]
        calcul = {
            "ENTREE": f"{stock_depart} + {m.quantite}",
            "SORTIE": f"{stock_depart} - {m.quantite}",
            "TRANSFERT": "inchange (interne)",
            "AJUSTEMENT": f"remplace par {m.quantite}",
        }[m.type_mouvement()]
        print(f"  {m.type_mouvement():<14} {signe:>5}   {calcul:<22} {nouveau:>13}")

    print("\n  --> Une seule ligne de code appelante :  m.appliquer(stock)")
    print("      4 comportements differents = POLYMORPHISME")


def demo_polymorphisme_roles():
    titre("3c. POLYMORPHISME - permissions() selon le role")

    utilisateurs = [
        Utilisateur("INVITE", login="invite", mot_de_passe_hash="x"),
        Vendeur("MUKENDI", prenom="Vente", login="vendeur", mot_de_passe_hash="x"),
        Gestionnaire("KABEYA", prenom="Gestion", login="gest", mot_de_passe_hash="x"),
        Admin("ADMIN", prenom="Super", login="admin", mot_de_passe_hash="x"),
    ]

    actions = ["consulter_produits", "creer_sortie",
               "creer_produit", "supprimer_utilisateur"]

    entete = f"  {'ROLE':<15} {'NB PERMS':>9}"
    for a in actions:
        entete += f" {a[:13]:>14}"
    print(entete)
    print("  " + "-" * 78)

    for u in utilisateurs:
        ligne = f"  {u.role():<15} {len(u.permissions()):>9}"
        for a in actions:
            ligne += f" {('OUI' if u.peut(a) else 'non'):>14}"
        print(ligne)

    print("\n  --> Meme appel  u.peut(action)  sans aucun 'if' cote appelant.")


# =====================================================================
# 4. ABSTRACTION
# =====================================================================
def demo_abstraction():
    titre("4. ABSTRACTION - impossible d'instancier une classe abstraite")

    print("  --> Tentative : Mouvement(produit_id=1, quantite=5, utilisateur_id=1)")
    try:
        Mouvement(produit_id=1, quantite=5, utilisateur_id=1)
    except TypeError as e:
        print(f"      REFUSE : {str(e)[:70]}")

    print("\n  --> Il faut passer par une classe concrete :")
    e = Entree(produit_id=1, quantite=5, utilisateur_id=1, entrepot_dest_id=1)
    print(f"      Entree creee : {e.libelle()}  (sens = {e.sens():+d})")


# =====================================================================
# 5. GESTION DES EXCEPTIONS METIER
# =====================================================================
def demo_exceptions():
    titre("5. EXCEPTIONS PERSONNALISEES du domaine")

    print("  --> Sortie de 500 unites alors que le stock est de 30 :")
    try:
        Sortie(produit_id=1, quantite=500,
               utilisateur_id=1, entrepot_source_id=1).appliquer(30)
    except StockInsuffisantError as e:
        print(f"      {e}")

    print("\n  --> Mouvement avec une quantite negative :")
    try:
        Entree(produit_id=1, quantite=-10, utilisateur_id=1, entrepot_dest_id=1)
    except QuantiteInvalideError as e:
        print(f"      {e}")

    print("\n  --> Produit avec une reference trop courte :")
    try:
        Produit("AB", "Test")
    except ValidationError as e:
        print(f"      {e}")

    print("\n  --> Ajustement sans motif :")
    try:
        Ajustement(produit_id=1, quantite=10, utilisateur_id=1).valider()
    except ValidationError as e:
        print(f"      {e}")


# =====================================================================
if __name__ == "__main__":
    print("\n" + "#" * 68)
    print("#  StockManager - DEMONSTRATION DES CONCEPTS POO")
    print("#" * 68)

    demo_encapsulation()
    demo_heritage()
    demo_polymorphisme_produits()
    demo_polymorphisme_mouvements()
    demo_polymorphisme_roles()
    demo_abstraction()
    demo_exceptions()

    print("\n" + "=" * 68)
    print("  DEMONSTRATION TERMINEE")
    print("=" * 68 + "\n")