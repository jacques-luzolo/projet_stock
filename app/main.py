import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
from datetime import datetime, date
import hashlib  # pour le hachage des mots de passe (simple démo)

# Configuration de la page
st.set_page_config(page_title="Gestion de Parc Automobile", page_icon="🚗", layout="wide")

# ===================================================================
# CONNEXION À MARIA DB
# ===================================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",          # Par défaut sous XAMPP
    "database": "gestion_stock",
    "charset": "utf8mb4"
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

# Initialisation / vérification de la connexion
def init_db():
    try:
        conn = get_connection()
        # On teste si la table utilisateurs existe
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM utilisateurs LIMIT 1")
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {e}")
        return False

if not init_db():
    st.stop()

# ===================================================================
# GESTION DE SESSION
# ===================================================================
if "connecte" not in st.session_state:
    st.session_state["connecte"] = False
    st.session_state["nom_user"] = ""
    st.session_state["role"] = ""
    st.session_state["user_id"] = None

def deconnexion():
    st.session_state["connecte"] = False
    st.session_state["nom_user"] = ""
    st.session_state["role"] = ""
    st.session_state["user_id"] = None
    st.rerun()

# ===================================================================
# AUTHENTIFICATION
# ===================================================================
if not st.session_state["connecte"]:
    st.title("🔐 Authentification")
    st.write("Connexion à l'espace de gestion")
    col1, _ = st.columns([1, 1])
    with col1:
        with st.form("login_form"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter")

            if submit:
                conn = get_connection()
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, nom, role, login, mot_de_passe FROM utilisateurs WHERE login = %s",
                        (username,)
                    )
                    user = cur.fetchone()
                conn.close()
                if user:
                    # Démo : mot de passe en clair (à adapter en prod)
                    if user[4] == password:
                        st.session_state["connecte"] = True
                        st.session_state["user_id"] = user[0]
                        st.session_state["nom_user"] = user[1]
                        st.session_state["role"] = user[2]
                        st.rerun()
                    else:
                        st.error("Mot de passe incorrect")
                else:
                    st.error("Utilisateur non trouvé")
        with st.expander("ℹ️ Comptes de démonstration"):
            st.write("🚗 Vendeur : `vendeur` / `vend123`")
            st.write("📊 Gestionnaire : `gestionnaire` / `gest123`")
            st.write("👑 Admin : `admin` / `admin123`")

# ===================================================================
# ESPACE CONNECTÉ
# ===================================================================
else:
    st.sidebar.title("📌 Session")
    st.sidebar.write(f"👤 **{st.session_state['nom_user']}**")
    st.sidebar.write(f"Rôle : `{st.session_state['role']}`")
    st.sidebar.button("🔴 Se déconnecter", on_click=deconnexion)

    # ------------------------------------------------------------
    # INTERFACE ADMINISTRATEUR
    # ------------------------------------------------------------
    if st.session_state["role"] == "Admin":
        st.title("👑 Espace Administrateur")

        tab1, tab2, tab3 = st.tabs(["🚗 Gestion Véhicules", "📝 Rapport Gestionnaire", "🧾 Ventes"])

        # --- Onglet 1 : Gestion des véhicules (Ajouter / Modifier / Supprimer)
        with tab1:
            st.subheader("Gestion des véhicules")
            conn = get_connection()
            df_vehicules = pd.read_sql_query("SELECT * FROM vehicules", conn)
            conn.close()

            col_ajout, col_modif_suppr = st.columns(2)

            # Ajouter
            with col_ajout:
                st.markdown("### ➕ Ajouter un véhicule")
                with st.form("form_ajout"):
                    marque = st.text_input("Marque")
                    modele = st.text_input("Modèle")
                    couleur = st.text_input("Couleur")
                    vitesse = st.number_input("Vitesse max (km/h)", min_value=0, value=200)
                    quantite = st.number_input("Quantité en stock", min_value=0, value=1)
                    prix = st.number_input("Prix unitaire (€)", min_value=0.0, value=10000.0, step=500.0)
                    seuil = st.number_input("Seuil minimum d'alerte", min_value=1, value=5)
                    date_pere = st.date_input("Date de péremption (facultatif)", value=None)
                    submit_ajout = st.form_submit_button("Ajouter")

                    if submit_ajout:
                        conn = get_connection()
                        with conn.cursor() as cur:
                            cur.execute("""
                                INSERT INTO vehicules (marque, modele, couleur, vitesse_max, quantite_stock, prix_unitaire, seuil_min, date_peremption)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (marque, modele, couleur, vitesse, quantite, prix, seuil, date_pere))
                            conn.commit()
                        conn.close()
                        st.success("Véhicule ajouté !")
                        st.rerun()

            # Modifier / Supprimer
            with col_modif_suppr:
                if not df_vehicules.empty:
                    st.markdown("### ✏️ Modifier / 🗑️ Supprimer")
                    select_vehicule = st.selectbox("Choisir un véhicule", df_vehicules["id"].astype(str) + " - " + df_vehicules["marque"] + " " + df_vehicules["modele"])
                    vehicule_id = int(select_vehicule.split(" - ")[0])
                    vehicule = df_vehicules[df_vehicules["id"] == vehicule_id].iloc[0]

                    with st.form("form_modif"):
                        marque_m = st.text_input("Marque", value=vehicule["marque"])
                        modele_m = st.text_input("Modèle", value=vehicule["modele"])
                        couleur_m = st.text_input("Couleur", value=vehicule["couleur"])
                        vitesse_m = st.number_input("Vitesse max", min_value=0, value=int(vehicule["vitesse_max"]))
                        quantite_m = st.number_input("Quantité", min_value=0, value=int(vehicule["quantite_stock"]))
                        prix_m = st.number_input("Prix unitaire", min_value=0.0, value=float(vehicule["prix_unitaire"]), step=500.0)
                        seuil_m = st.number_input("Seuil minimal", min_value=1, value=int(vehicule["seuil_min"]))
                        submit_modif = st.form_submit_button("Mettre à jour")
                        if submit_modif:
                            conn = get_connection()
                            with conn.cursor() as cur:
                                cur.execute("""
                                    UPDATE vehicules SET marque=%s, modele=%s, couleur=%s, vitesse_max=%s,
                                    quantite_stock=%s, prix_unitaire=%s, seuil_min=%s
                                    WHERE id=%s
                                """, (marque_m, modele_m, couleur_m, vitesse_m, quantite_m, prix_m, seuil_m, vehicule_id))
                                conn.commit()
                            conn.close()
                            st.success("Modifié avec succès")
                            st.rerun()

                    if st.button("🗑️ Supprimer ce véhicule"):
                        conn = get_connection()
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM vehicules WHERE id=%s", (vehicule_id,))
                            conn.commit()
                        conn.close()
                        st.warning("Véhicule supprimé")
                        st.rerun()
                else:
                    st.info("Aucun véhicule en base.")

            st.dataframe(df_vehicules, use_container_width=True, hide_index=True)

        # --- Onglet 2 : Visualiser le rapport rédigé par le gestionnaire
        with tab2:
            st.subheader("Dernier rapport du gestionnaire")
            conn = get_connection()
            df_rapport = pd.read_sql_query("SELECT * FROM rapports ORDER BY date_rapport DESC LIMIT 1", conn)
            conn.close()
            if not df_rapport.empty:
                st.write("**Date :**", df_rapport.iloc[0]["date_rapport"])
                st.write("**Contenu :**")
                st.markdown(df_rapport.iloc[0]["contenu_texte"])
            else:
                st.info("Aucun rapport disponible.")

        # --- Onglet 3 : Historique des ventes
        with tab3:
            st.subheader("Ventes enregistrées")
            conn = get_connection()
            df_ventes = pd.read_sql_query("""
                SELECT v.date_vente, veh.marque, veh.modele, v.quantite, v.prix_unitaire, v.prix_total, u.nom AS vendeur
                FROM ventes v
                JOIN vehicules veh ON v.vehicule_id = veh.id
                JOIN utilisateurs u ON v.vendeur_id = u.id
                ORDER BY v.date_vente DESC
            """, conn)
            conn.close()
            st.dataframe(df_ventes, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------
    # INTERFACE GESTIONNAIRE
    # ------------------------------------------------------------
    elif st.session_state["role"] == "Gestionnaire":
        st.title("📊 Espace Gestionnaire")

        tab1, tab2, tab3 = st.tabs(["🚗 Gérer Véhicules", "📦 Mouvements de stock", "📝 Rédiger Rapport"])

        # --- Onglet 1 : Gestion des véhicules (avec recherche)
        with tab1:
            st.subheader("Gestion des véhicules")
            conn = get_connection()
            df_vehicules = pd.read_sql_query("SELECT * FROM vehicules", conn)
            conn.close()

            # Recherche
            recherche = st.text_input("🔍 Rechercher par marque ou modèle", "")
            if recherche:
                df_vehicules = df_vehicules[
                    df_vehicules["marque"].str.contains(recherche, case=False, na=False) |
                    df_vehicules["modele"].str.contains(recherche, case=False, na=False)
                ]

            st.dataframe(df_vehicules, use_container_width=True, hide_index=True)

            col_ajout, col_modif_suppr = st.columns(2)

            with col_ajout:
                st.markdown("### ➕ Ajouter un véhicule")
                with st.form("form_ajout_g"):
                    marque = st.text_input("Marque")
                    modele = st.text_input("Modèle")
                    couleur = st.text_input("Couleur")
                    vitesse = st.number_input("Vitesse max", min_value=0, value=200)
                    quantite = st.number_input("Quantité", min_value=0, value=1)
                    prix = st.number_input("Prix unitaire", min_value=0.0, value=10000.0, step=500.0)
                    seuil = st.number_input("Seuil minimum", min_value=1, value=5)
                    submit_ajout = st.form_submit_button("Ajouter")
                    if submit_ajout:
                        try:
                            conn = get_connection()
                            with conn.cursor() as cur:
                                cur.execute("""
                                    INSERT INTO vehicules (marque, modele, couleur, vitesse_max, quantite_stock, prix_unitaire, seuil_min)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """, (marque, modele, couleur, vitesse, quantite, prix, seuil))
                                conn.commit()
                            conn.close()
                            st.success("Véhicule ajouté")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            with col_modif_suppr:
                if not df_vehicules.empty:
                    st.markdown("### ✏️ Modifier / Supprimer")
                    select_v = st.selectbox("Choisir", df_vehicules["id"].astype(str) + " - " + df_vehicules["marque"] + " " + df_vehicules["modele"])
                    v_id = int(select_v.split(" - ")[0])
                    v = df_vehicules[df_vehicules["id"] == v_id].iloc[0]

                    with st.form("form_modif_g"):
                        marque_m = st.text_input("Marque", value=v["marque"])
                        modele_m = st.text_input("Modèle", value=v["modele"])
                        couleur_m = st.text_input("Couleur", value=v["couleur"])
                        vitesse_m = st.number_input("Vitesse", min_value=0, value=int(v["vitesse_max"]))
                        quantite_m = st.number_input("Quantité", min_value=0, value=int(v["quantite_stock"]))
                        prix_m = st.number_input("Prix", min_value=0.0, value=float(v["prix_unitaire"]), step=500.0)
                        seuil_m = st.number_input("Seuil", min_value=1, value=int(v["seuil_min"]))
                        submit_m = st.form_submit_button("Modifier")
                        if submit_m:
                            conn = get_connection()
                            with conn.cursor() as cur:
                                cur.execute("""
                                    UPDATE vehicules SET marque=%s, modele=%s, couleur=%s, vitesse_max=%s,
                                    quantite_stock=%s, prix_unitaire=%s, seuil_min=%s WHERE id=%s
                                """, (marque_m, modele_m, couleur_m, vitesse_m, quantite_m, prix_m, seuil_m, v_id))
                                conn.commit()
                            conn.close()
                            st.success("Modifié")
                            st.rerun()

                    if st.button("Supprimer ce véhicule"):
                        conn = get_connection()
                        with conn.cursor() as cur:
                            cur.execute("DELETE FROM vehicules WHERE id=%s", (v_id,))
                            conn.commit()
                        conn.close()
                        st.warning("Supprimé")
                        st.rerun()

        # --- Onglet 2 : Mouvement du stock (entrées / sorties) + véhicules vendus
        with tab2:
            st.subheader("Gestion des entrées / sorties de stock")

            # Alerte si stock < seuil (seuil = 5 par défaut)
            conn = get_connection()
            df_alert = pd.read_sql_query("""
                SELECT marque, modele, quantite_stock, seuil_min
                FROM vehicules
                WHERE quantite_stock <= seuil_min
            """, conn)
            conn.close()
            if not df_alert.empty:
                st.error("🚨 **Alerte stock bas (seuil ≤ 5)**")
                st.dataframe(df_alert, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Aucun véhicule sous le seuil d'alerte.")

            # Enregistrer une entrée ou une sortie
            conn = get_connection()
            df_veh = pd.read_sql_query("SELECT * FROM vehicules", conn)
            conn.close()
            if not df_veh.empty:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### 📥 Entrée de stock")
                    with st.form("form_entree"):
                        veh_select = st.selectbox("Véhicule", df_veh["id"].astype(str) + " - " + df_veh["marque"] + " " + df_veh["modele"])
                        veh_id = int(veh_select.split(" - ")[0])
                        qte_entree = st.number_input("Quantité entrée", min_value=1, value=1)
                        submit_entree = st.form_submit_button("Enregistrer l'entrée")
                        if submit_entree:
                            conn = get_connection()
                            with conn.cursor() as cur:
                                # Mise à jour du stock
                                cur.execute("UPDATE vehicules SET quantite_stock = quantite_stock + %s WHERE id = %s", (qte_entree, veh_id))
                                # Journal de mouvement
                                cur.execute("""
                                    INSERT INTO mouvements_stock (vehicule_id, type_mouvement, quantite, responsable)
                                    VALUES (%s, 'entree', %s, %s)
                                """, (veh_id, qte_entree, st.session_state["nom_user"]))
                                conn.commit()
                            conn.close()
                            st.success("Entrée enregistrée")
                            st.rerun()

                with col2:
                    st.markdown("### 📤 Sortie de stock")
                    with st.form("form_sortie"):
                        veh_select2 = st.selectbox("Véhicule (sortie)", df_veh["id"].astype(str) + " - " + df_veh["marque"] + " " + df_veh["modele"])
                        veh_id2 = int(veh_select2.split(" - ")[0])
                        max_qte = int(df_veh[df_veh["id"] == veh_id2]["quantite_stock"].iloc[0])
                        if max_qte == 0:
                            st.warning("Stock actuel à 0, aucune sortie possible.")
                        else:
                            qte_sortie = st.number_input("Quantité sortie", min_value=1, max_value=max_qte, value=1)
                            submit_sortie = st.form_submit_button("Enregistrer la sortie")
                            if submit_sortie:
                                conn = get_connection()
                                with conn.cursor() as cur:
                                    cur.execute("UPDATE vehicules SET quantite_stock = quantite_stock - %s WHERE id = %s", (qte_sortie, veh_id2))
                                    cur.execute("""
                                        INSERT INTO mouvements_stock (vehicule_id, type_mouvement, quantite, responsable)
                                        VALUES (%s, 'sortie', %s, %s)
                                    """, (veh_id2, qte_sortie, st.session_state["nom_user"]))
                                    conn.commit()
                                conn.close()
                                st.success("Sortie enregistrée")
                                st.rerun()

            st.markdown("---")
            st.subheader("🧾 Véhicules vendus (Date, heure, marque, prix unitaire, prix total)")
            conn = get_connection()
            df_ventes_g = pd.read_sql_query("""
                SELECT v.date_vente, veh.marque, veh.modele, v.quantite, v.prix_unitaire, v.prix_total, u.nom AS vendeur
                FROM ventes v
                JOIN vehicules veh ON v.vehicule_id = veh.id
                JOIN utilisateurs u ON v.vendeur_id = u.id
                ORDER BY v.date_vente DESC
            """, conn)
            conn.close()
            st.dataframe(df_ventes_g, use_container_width=True, hide_index=True)

            # Affichage de l'historique des mouvements
            with st.expander("📋 Détail de tous les mouvements de stock"):
                conn = get_connection()
                df_mvts = pd.read_sql_query("""
                    SELECT m.date_mouvement, m.type_mouvement, m.quantite, m.responsable, veh.marque, veh.modele
                    FROM mouvements_stock m
                    JOIN vehicules veh ON m.vehicule_id = veh.id
                    ORDER BY m.date_mouvement DESC
                """, conn)
                conn.close()
                st.dataframe(df_mvts, use_container_width=True, hide_index=True)

        # --- Onglet 3 : Rédaction de rapport avec diagramme de Pareto
        with tab3:
            st.subheader("Rédaction du rapport")

            # Diagramme de Pareto : nombre de véhicules vendus par vendeur
            st.markdown("### 📊 Diagramme de Pareto – Ventes par vendeur")
            conn = get_connection()
            df_ventes_pareto = pd.read_sql_query("""
                SELECT u.nom AS vendeur, COUNT(v.id) AS nb_ventes, SUM(v.prix_total) AS total_ventes
                FROM ventes v
                JOIN utilisateurs u ON v.vendeur_id = u.id
                GROUP BY u.nom
                ORDER BY nb_ventes DESC
            """, conn)
            conn.close()

            if not df_ventes_pareto.empty:
                # Calcul du pourcentage cumulé
                df_ventes_pareto["cumul"] = df_ventes_pareto["nb_ventes"].cumsum()
                df_ventes_pareto["cumul_pct"] = 100 * df_ventes_pareto["cumul"] / df_ventes_pareto["nb_ventes"].sum()

                fig = px.bar(df_ventes_pareto, x='vendeur', y='nb_ventes', title="Ventes par vendeur (Pareto)")
                fig.add_scatter(x=df_ventes_pareto['vendeur'], y=df_ventes_pareto['cumul_pct'],
                                yaxis='y2', name='% cumulé', mode='lines+markers')
                fig.update_layout(yaxis2=dict(title='% cumulé', overlaying='y', side='right'))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Pas encore de ventes.")

            # Zone de texte pour rédiger le rapport
            st.markdown("### 📝 Contenu du rapport")
            rapport_contenu = st.text_area("Texte libre du rapport", height=200,
                                           placeholder="Rédigez ici votre analyse, synthèse, etc.")

            # Zone de péremption (texte libre)
            st.markdown("### ⏰ Péremption des véhicules")
            info_peremption = st.text_area("Informations sur les péremptions (zone de texte)", height=100)

            if st.button("💾 Enregistrer le rapport"):
                if rapport_contenu.strip():
                    conn = get_connection()
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO rapports (gestionnaire_id, contenu_texte)
                            VALUES (%s, %s)
                        """, (st.session_state["user_id"], rapport_contenu + "\n\n[Péremption] : " + info_peremption))
                        conn.commit()
                    conn.close()
                    st.success("Rapport enregistré !")
                else:
                    st.warning("Le rapport est vide.")

    # ------------------------------------------------------------
    # INTERFACE VENDEUR
    # ------------------------------------------------------------
    elif st.session_state["role"] == "Vendeur":
        st.title("🛒 Espace Vendeur")

        # Visualisation des véhicules disponibles
        st.subheader("🚗 Véhicules disponibles")
        conn = get_connection()
        df_vehicules = pd.read_sql_query("""
            SELECT marque, modele, couleur, vitesse_max, quantite_stock, prix_unitaire
            FROM vehicules
            WHERE quantite_stock > 0
        """, conn)
        conn.close()
        st.dataframe(df_vehicules, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Effectuer une vente
        st.subheader("💵 Effectuer une vente")
        conn = get_connection()
        df_veh = pd.read_sql_query("SELECT * FROM vehicules WHERE quantite_stock > 0", conn)
        conn.close()

        if not df_veh.empty:
            col1, col2 = st.columns(2)

            with col1:
                vente_vehicule = st.selectbox("Sélectionner le véhicule",
                                              df_veh["id"].astype(str) + " - " + df_veh["marque"] + " " + df_veh["modele"])
                vehicule_id = int(vente_vehicule.split(" - ")[0])
                vehicule = df_veh[df_veh["id"] == vehicule_id].iloc[0]

                stock_dispo = int(vehicule["quantite_stock"])
                prix_unitaire = float(vehicule["prix_unitaire"])

                quantite = st.number_input("Quantité à vendre", min_value=1, max_value=stock_dispo, value=1)
                total = quantite * prix_unitaire
                st.write(f"💰 **Total à payer :** `{total:.2f} €`")

            with col2:
                st.markdown("### 📋 Récapitulatif")
                st.write(f"**Véhicule :** {vehicule['marque']} {vehicule['modele']}")
                st.write(f"**Couleur :** {vehicule['couleur']}")
                st.write(f"**Vitesse max :** {vehicule['vitesse_max']} km/h")
                st.write(f"**Prix unitaire :** {prix_unitaire:.2f} €")
                st.write(f"**Quantité :** {quantite}")

            if st.button("✅ Valider la vente"):
                try:
                    conn = get_connection()
                    with conn.cursor() as cur:
                        # Enregistrer la vente
                        cur.execute("""
                            INSERT INTO ventes (vehicule_id, date_vente, quantite, prix_unitaire, prix_total, vendeur_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (vehicule_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quantite,
                              prix_unitaire, total, st.session_state["user_id"]))
                        # Mettre à jour le stock
                        cur.execute("UPDATE vehicules SET quantite_stock = quantite_stock - %s WHERE id = %s",
                                    (quantite, vehicule_id))
                        # Enregistrer le mouvement de sortie
                        cur.execute("""
                            INSERT INTO mouvements_stock (vehicule_id, type_mouvement, quantite, responsable)
                            VALUES (%s, 'sortie', %s, %s)
                        """, (vehicule_id, quantite, st.session_state["nom_user"]))
                        conn.commit()
                    conn.close()
                    st.success("Vente enregistrée avec succès !")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
        else:
            st.info("Aucun véhicule en stock.")

        # Mise à jour de l'affichage après vente
        st.markdown("---")
        st.subheader("📄 Historique de vos ventes")
        conn = get_connection()
        df_ventes = pd.read_sql_query("""
            SELECT v.date_vente, veh.marque, veh.modele, v.quantite, v.prix_unitaire, v.prix_total
            FROM ventes v
            JOIN vehicules veh ON v.vehicule_id = veh.id
            WHERE v.vendeur_id = %s
            ORDER BY v.date_vente DESC
        """, conn, params=(st.session_state["user_id"],))
        conn.close()
        st.dataframe(df_ventes, use_container_width=True, hide_index=True)
