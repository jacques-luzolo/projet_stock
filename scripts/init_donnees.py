"""Script d initialisation : utilisateurs, produits et stocks de test."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.connection import db
from src.utils.security import hacher_mot_de_passe


def creer_utilisateurs():
    comptes = [
        ("ADMIN", "Super", "admin@stock.cd", "admin", "Admin@2025", "admin"),
        ("KABEYA", "Gestion", "gest@stock.cd", "gestionnaire", "Gest@2025", "gestionnaire"),
        ("MUKENDI", "Vente", "vend@stock.cd", "vendeur", "Vend@2025", "vendeur"),
    ]
    with db.curseur(commit=True) as cur:
        for nom, prenom, email, login, mdp, role in comptes:
            cur.execute("SELECT id FROM roles WHERE nom = ?", (role,))
            ligne = cur.fetchone()
            if not ligne:
                continue
            cur.execute(
                """INSERT IGNORE INTO utilisateurs
                   (nom, prenom, email, login, mot_de_passe_hash, role_id)
                   VALUES (?,?,?,?,?,?)""",
                (nom, prenom, email, login, hacher_mot_de_passe(mdp), ligne["id"]))
            print(f"   {login} / {mdp}")


def creer_produits():
    produits = [
        ("INF-001","Ordinateur portable HP",1,1,"pcs",850.00,1050.00,5,50,0,None),
        ("INF-002","Souris sans fil Logitech",1,1,"pcs",12.00,20.00,20,200,0,None),
        ("INF-003","Clavier mecanique",1,1,"pcs",35.00,55.00,10,100,0,None),
        ("BUR-001","Ramette papier A4",2,2,"ramette",4.50,7.00,50,500,0,None),
        ("BUR-002","Stylo bille bleu",2,2,"boite",2.00,4.00,30,300,0,None),
        ("ALI-001","Lait UHT 1L",3,3,"brique",1.20,2.00,100,1000,1,"2026-12-31"),
        ("ALI-002","Riz parfume 25kg",3,3,"sac",28.00,38.00,10,100,1,"2027-06-30"),
        ("HYG-001","Savon liquide 5L",4,4,"bidon",8.00,13.00,15,150,0,None),
    ]
    with db.curseur(commit=True) as cur:
        for p in produits:
            cur.execute(
                """INSERT IGNORE INTO produits
                   (reference,designation,categorie_id,fournisseur_id,unite,
                    prix_achat,prix_vente,seuil_min,seuil_max,perissable,date_peremption)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""", p)
            print(f"   {p[0]} - {p[1]}")


def initialiser_stocks():
    with db.curseur(commit=True) as cur:
        cur.execute("SELECT id FROM produits")
        produits = [r["id"] for r in cur.fetchall()]
        cur.execute("SELECT id FROM entrepots")
        entrepots = [r["id"] for r in cur.fetchall()]
        for pid in produits:
            for eid in entrepots:
                cur.execute(
                    "INSERT IGNORE INTO stocks (produit_id,entrepot_id,quantite) VALUES (?,?,?)",
                    (pid, eid, random.randint(0, 120)))
    print("   stocks initialises")


if __name__ == "__main__":
    print("Initialisation StockManager\n")
    print("[1] Utilisateurs"); creer_utilisateurs()
    print("\n[2] Produits");    creer_produits()
    print("\n[3] Stocks");      initialiser_stocks()
    print("\nTermine ! Connexion : admin / Admin@2025")
