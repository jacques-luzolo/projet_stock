import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Système de Gestion de Stock", page_icon="📦", layout="wide")

# ===================================================================
# FONCTION DE CONNEXION À LA BASE DE DONNÉES SQL
# ===================================================================
def get_db_connection():
    # Remarque : Si vous utilisez SQLite (fichier local/distant) :
    db_path = os.path.join(os.path.dirname(__file__), "..", "sql", "projet_stock.db")
    
    # Si le fichier sqlite n'existe pas encore, on se connecte en mémoire/fichier
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialisation des tables si elles n'existent pas encore
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table Produits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prix REAL NOT NULL,
            quantite INTEGER NOT NULL,
            seuil_min INTEGER NOT NULL
        )
    ''')
    
    # Table Ventes / Mouvements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_vente TEXT NOT NULL,
            produit TEXT NOT NULL,
            quantite INTEGER NOT NULL,
            total REAL NOT NULL,
            vendeur TEXT NOT NULL
        )
    ''')
    
    # Insertion de quelques données initiales si la table est vide
    cursor.execute("SELECT COUNT(*) FROM produits")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO produits (nom, prix, quantite, seuil_min)
            VALUES (?, ?, ?, ?)
        ''', [
            ("Ordinateur Portable Dell", 850.00, 15, 5),
            ("Souris Sans Fil", 25.50, 4, 10),
            ("Clavier Mécanique", 60.00, 22, 5),
            ("Écran 27 pouces", 210.00, 2, 4)
        ])
    
    conn.commit()
    conn.close()

# Exécuter l'initialisation BDD
init_db()

# --- INITIALISATION DE LA SESSION USER ---
if "connecte" not in st.session_state:
    st.session_state["connecte"] = False
    st.session_state["nom_user"] = ""
    st.session_state["role"] = ""

def deconnexion():
    st.session_state["connecte"] = False
    st.session_state["nom_user"] = ""
    st.session_state["role"] = ""
    st.rerun()

# ===================================================================
# 1. AUTHENTIFICATION (LOGIN)
# ===================================================================
if not st.session_state["connecte"]:
    st.title("🔐 Connexion - Base de Données Sécurisée")
    st.write("Connectez-vous avec votre rôle pour accéder à la base de données.")

    col1, _ = st.columns([1, 1])
    with col1:
        with st.form("form_login"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("🚀 Se connecter")

            if submit:
                if username == "vendeur" and password == "vend123":
                    st.session_state["connecte"] = True
                    st.session_state["nom_user"] = "Jean (Vendeur)"
                    st.session_state["role"] = "Vendeur"
                    st.rerun()
                elif username == "gestionnaire" and password == "gest123":
                    st.session_state["connecte"] = True
                    st.session_state["nom_user"] = "Marie (Gestionnaire)"
                    st.session_state["role"] = "Gestionnaire"
                    st.rerun()
                elif username == "admin" and password == "admin123":
                    st.session_state["connecte"] = True
                    st.session_state["nom_user"] = "Alex (Admin)"
                    st.session_state["role"] = "Admin"
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects.")

        with st.expander("ℹ️ Comptes de démonstration"):
            st.write("🛒 **Vendeur :** `vendeur` / `vend123`")
            st.write("📊 **Gestionnaire :** `gestionnaire` / `gest123`")
            st.write("👑 **Admin :** `admin` / `admin123`")

# ===================================================================
# 2. ESPACES SPÉCIFIQUES AVEC PERSISTANCE SQL
# ===================================================================
else:
    st.sidebar.title("📌 Session")
    st.sidebar.write(f"👤 **Utilisateur :** {st.session_state['nom_user']}")
    st.sidebar.write(f"🎭 **Rôle :** `{st.session_state['role']}`")
    st.sidebar.button("🔴 Se déconnecter", on_click=deconnexion)
    st.sidebar.markdown("---")

    conn = get_db_connection()

    # ----------------------------------------------------------------
    # 🛒 CAS 1 : ESPACE VENDEUR (Enregistrement SQL direct)
    # ----------------------------------------------------------------
    if st.session_state["role"] == "Vendeur":
        st.title("🛒 Espace Vente (Caisse - Connexion BDD)")

        col_vente, col_dispo = st.columns([1, 1])

        # Chargement des produits depuis SQL
        df_prod = pd.read_sql_query("SELECT * FROM produits WHERE quantite > 0", conn)

        with col_vente:
            st.subheader("📝 Nouvelle Vente")
            
            if not df_prod.empty:
                produit_choisi = st.selectbox("Sélectionner le produit", df_prod["nom"].tolist())
                
                ligne = df_prod[df_prod["nom"] == produit_choisi].iloc[0]
                stock_max = int(ligne["quantite"])
                prix_unitaire = float(ligne["prix"])

                quantite_vente = st.number_input("Quantité à vendre", min_value=1, max_value=stock_max, value=1)
                total_prix = quantite_vente * prix_unitaire

                st.write(f"💰 **Total à encaisser :** `{total_prix:.2f} €`")

                if st.button("✅ Valider & Enregistrer dans la BDD"):
                    cursor = conn.cursor()
                    
                    # 1. Mise à jour du stock dans la BDD SQL
                    cursor.execute("UPDATE produits SET quantite = quantite - ? WHERE nom = ?", (quantite_vente, produit_choisi))
                    
                    # 2. Insertion de la vente dans la BDD SQL
                    cursor.execute(
                        "INSERT INTO ventes (date_vente, produit, quantite, total, vendeur) VALUES (?, ?, ?, ?, ?)",
                        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), produit_choisi, quantite_vente, total_prix, st.session_state["nom_user"])
                    )
                    
                    conn.commit()
                    st.success("✅ Vente enregistrée avec succès dans la Base de Données !")
                    st.rerun()
            else:
                st.error("Aucun produit en stock.")

        with col_dispo:
            st.subheader("🔍 Stocks en Base de Données")
            st.dataframe(df_prod[["nom", "prix", "quantite"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🧾 Vos ventes enregistrées en BDD")
        df_ventes = pd.read_sql_query("SELECT * FROM ventes ORDER BY id DESC", conn)
        st.dataframe(df_ventes, use_container_width=True, hide_index=True)

    # ----------------------------------------------------------------
    # 📊 CAS 2 : ESPACE GESTIONNAIRE (Consultation SQL & Alertes)
    # ----------------------------------------------------------------
    elif st.session_state["role"] == "Gestionnaire":
        st.title("📊 Espace Gestionnaire - Stocks en BDD")

        df_prod = pd.read_sql_query("SELECT * FROM produits", conn)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Références BDD", len(df_prod))
        m2.metric("Valeur Totale Stock", f"{sum(df_prod['prix'] * df_prod['quantite']):,.2f} €")
        
        alertes = df_prod[df_prod["quantite"] <= df_prod["seuil_min"]]
        m3.metric("🚨 Alertes de Stock", len(alertes))

        st.markdown("---")
        st.subheader("📦 Table `produits` (Vue SQL direct)")
        st.dataframe(df_prod, use_container_width=True, hide_index=True)

        if not alertes.empty:
            st.error("⚠️ **Produits sous le seuil critique (Alerte BDD) :**")
            st.dataframe(alertes[["nom", "quantite", "seuil_min"]], use_container_width=True, hide_index=True)

    # ----------------------------------------------------------------
    # 👑 CAS 3 : ESPACE ADMINISTRATEUR (Vue BDD Globale)
    # ----------------------------------------------------------------
    elif st.session_state["role"] == "Admin":
        st.title("👑 Espace Administrateur - Base de Données")

        tab1, tab2 = st.tabs(["📦 Table Produits", "🧾 Table Ventes"])

        with tab1:
            df_p = pd.read_sql_query("SELECT * FROM produits", conn)
            st.dataframe(df_p, use_container_width=True, hide_index=True)

        with tab2:
            df_v = pd.read_sql_query("SELECT * FROM ventes", conn)
            st.dataframe(df_v, use_container_width=True, hide_index=True)

    conn.close()