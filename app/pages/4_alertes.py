import streamlit as st

st.set_page_config(page_title="Alertes de Stock", page_icon="🚨")

st.title("🚨 Alertes & Seuils de Stock")
st.write("Bienvenue sur le module de gestion des alertes.")

# Exemple de tableau d'alertes
st.subheader("⚠️ Produits sous le seuil minimum")

# Exemple visuel
st.error("Produit : Clavier USB | Stock actuel : 2 | Seuil mini : 5")
st.warning("Produit : Souris Sans Fil | Stock actuel : 4 | Seuil mini : 10")