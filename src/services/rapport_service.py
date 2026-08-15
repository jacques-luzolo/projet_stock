"""Service de generation de rapports et d'exports (CSV, Excel, PDF)."""
import io
import re
from datetime import datetime
from decimal import Decimal

import pandas as pd

from src.exceptions.domain_exceptions import StockAppError
from src.repositories.fournisseur_repository import EntrepotRepository
from src.repositories.mouvement_repository import MouvementRepository
from src.repositories.produit_repository import ProduitRepository
from src.utils.logger import logger


class RapportService:
    """Produit les jeux de donnees et les fichiers exportables."""

    # Colonnes attendues quand un rapport ne retourne aucune ligne
    COLONNES_VIDES = {
        "inventaire": ["reference", "designation", "categorie", "fournisseur",
                       "quantite_totale", "seuil_min", "prix_achat",
                       "prix_vente", "valeur_stock"],
        "sous_seuil": ["reference", "designation", "quantite_totale",
                       "seuil_min", "fournisseur"],
        "categorie": ["categorie", "valeur", "quantite", "nb_produits"],
        "entrepot": ["nom", "localisation", "quantite", "valeur",
                     "nb_references"],
        "mouvements": ["date_mouvement", "type_mouvement", "reference",
                       "designation", "quantite", "utilisateur", "montant"],
    }

    def __init__(self):
        self.produits = ProduitRepository()
        self.mouvements = MouvementRepository()
        self.entrepots = EntrepotRepository()

    # ================================================================
    # Utilitaires internes
    # ================================================================
    @staticmethod
    def _construire(lignes, cle_colonnes):
        """
        Cree un DataFrame propre meme si la requete ne retourne rien.
        Evite les KeyError dans l'interface.
        """
        colonnes = RapportService.COLONNES_VIDES.get(cle_colonnes, [])
        if not lignes:
            return pd.DataFrame(columns=colonnes)
        return RapportService._normaliser(pd.DataFrame(lignes))

    @staticmethod
    def _normaliser(df):
        """
        Convertit les types SQL en types Python exploitables :
          - Decimal -> float  (sinon Plotly et Excel echouent)
          - date / datetime -> conserves mais sans fuseau
        """
        if df.empty:
            return df

        for colonne in df.columns:
            echantillon = df[colonne].dropna()
            if echantillon.empty:
                continue
            if isinstance(echantillon.iloc[0], Decimal):
                df[colonne] = df[colonne].astype(float)

        return df

    @staticmethod
    def _nettoyer_nom_feuille(nom):
        """Excel interdit  [ ] : * ? / \\  et limite a 31 caracteres."""
        nom = re.sub(r"[\[\]:*?/\\]", "-", str(nom or "Rapport"))
        return nom.strip()[:31] or "Rapport"

    # ================================================================
    # Jeux de donnees
    # ================================================================
    def inventaire(self, actifs_seulement=True):
        """Inventaire complet valorise."""
        try:
            return self._construire(
                self.produits.lister_avec_stock(actifs_seulement), "inventaire")
        except StockAppError as err:
            logger.error("Rapport inventaire : %s", err)
            return pd.DataFrame(columns=self.COLONNES_VIDES["inventaire"])

    def sous_seuil(self):
        """Produits dont le stock est au niveau ou sous le seuil minimum."""
        try:
            return self._construire(
                self.produits.produits_sous_seuil(), "sous_seuil")
        except StockAppError as err:
            logger.error("Rapport sous_seuil : %s", err)
            return pd.DataFrame(columns=self.COLONNES_VIDES["sous_seuil"])

    def valeur_par_categorie(self):
        """Repartition de la valeur du stock par categorie."""
        try:
            return self._construire(
                self.produits.valeur_par_categorie(), "categorie")
        except StockAppError as err:
            logger.error("Rapport categories : %s", err)
            return pd.DataFrame(columns=self.COLONNES_VIDES["categorie"])

    def stock_par_entrepot(self):
        """Quantites et valeurs par entrepot."""
        try:
            return self._construire(
                self.entrepots.stock_par_entrepot(), "entrepot")
        except StockAppError as err:
            logger.error("Rapport entrepots : %s", err)
            return pd.DataFrame(columns=self.COLONNES_VIDES["entrepot"])

    def historique_mouvements(self, jours=30, limite=500):
        """
        Historique des mouvements des N derniers jours.

        CORRECTION : le parametre 'jours' est desormais reellement applique
        (filtrage sur la colonne date_mouvement).
        """
        try:
            df = self._construire(
                self.mouvements.historique(limite=limite), "mouvements")

            if not df.empty and jours and "date_mouvement" in df.columns:
                df["date_mouvement"] = pd.to_datetime(df["date_mouvement"],
                                                      errors="coerce")
                limite_date = pd.Timestamp.now() - pd.Timedelta(days=int(jours))
                df = df[df["date_mouvement"] >= limite_date]

            return df.reset_index(drop=True)
        except StockAppError as err:
            logger.error("Rapport mouvements : %s", err)
            return pd.DataFrame(columns=self.COLONNES_VIDES["mouvements"])

    def evolution(self, jours=30):
        """Serie temporelle des mouvements (pour les graphiques)."""
        try:
            lignes = self.mouvements.evolution_journaliere(jours)
            if not lignes:
                return pd.DataFrame(columns=["jour", "type_mouvement", "quantite"])
            df = self._normaliser(pd.DataFrame(lignes))
            df["jour"] = pd.to_datetime(df["jour"], errors="coerce")
            return df
        except StockAppError as err:
            logger.error("Rapport evolution : %s", err)
            return pd.DataFrame(columns=["jour", "type_mouvement", "quantite"])

    def synthese(self):
        """Indicateurs cles du tableau de bord."""
        try:
            return self.produits.statistiques()
        except StockAppError as err:
            logger.error("Synthese : %s", err)
            return {"nb_produits": 0, "unites_totales": 0, "valeur_totale": 0,
                    "nb_sous_seuil": 0, "nb_ruptures": 0}

    # ================================================================
    # Exports
    # ================================================================
    @staticmethod
    def vers_csv(df):
        """Export CSV (BOM UTF-8 pour un affichage correct dans Excel)."""
        if df is None or df.empty:
            df = pd.DataFrame({"info": ["Aucune donnee"]})
        return df.to_csv(index=False, sep=";").encode("utf-8-sig")

    @staticmethod
    def vers_excel(df, nom_feuille="Rapport"):
        """Export Excel avec largeur de colonnes ajustee."""
        if df is None or df.empty:
            df = pd.DataFrame({"info": ["Aucune donnee"]})

        nom_feuille = RapportService._nettoyer_nom_feuille(nom_feuille)
        tampon = io.BytesIO()

        with pd.ExcelWriter(tampon, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=nom_feuille)
            feuille = writer.sheets[nom_feuille]

            # Ajustement automatique de la largeur des colonnes
            for i, colonne in enumerate(df.columns, start=1):
                longueur_max = max(
                    len(str(colonne)),
                    df[colonne].astype(str).str.len().max() if len(df) else 0,
                )
                lettre = feuille.cell(row=1, column=i).column_letter
                feuille.column_dimensions[lettre].width = min(longueur_max + 3, 45)

        return tampon.getvalue()

    @staticmethod
    def vers_pdf(df, titre="Rapport StockManager", max_lignes=50,
                 max_colonnes=9):
        """
        Genere un PDF paysage avec ReportLab.

        CORRECTIONS :
          - gestion du DataFrame vide
          - limitation du nombre de colonnes (evite le debordement)
          - largeurs de colonnes calculees
          - pied de page indiquant les lignes tronquees
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                        Table, TableStyle)

        styles = getSampleStyleSheet()
        tampon = io.BytesIO()
        doc = SimpleDocTemplate(
            tampon, pagesize=landscape(A4),
            leftMargin=1.2 * cm, rightMargin=1.2 * cm,
            topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        )

        elements = [
            Paragraph(str(titre), styles["Title"]),
            Paragraph(f"StockManager - genere le "
                      f"{datetime.now():%d/%m/%Y a %H:%M}", styles["Normal"]),
            Spacer(1, 14),
        ]

        # -------- cas du rapport vide --------
        if df is None or df.empty:
            elements.append(Paragraph("Aucune donnee disponible pour ce rapport.",
                                      styles["Normal"]))
            doc.build(elements)
            return tampon.getvalue()

        # -------- troncature raisonnee --------
        total_lignes = len(df)
        total_colonnes = len(df.columns)

        apercu = df.iloc[:max_lignes, :max_colonnes].copy()

        # Formatage lisible des nombres et des dates
        for colonne in apercu.columns:
            if pd.api.types.is_float_dtype(apercu[colonne]):
                apercu[colonne] = apercu[colonne].map(lambda v: f"{v:,.2f}"
                                                      .replace(",", " "))
            elif pd.api.types.is_datetime64_any_dtype(apercu[colonne]):
                apercu[colonne] = apercu[colonne].dt.strftime("%d/%m/%Y %H:%M")
        apercu = apercu.astype(str)

        donnees = [list(apercu.columns)] + apercu.values.tolist()

        largeur_utile = landscape(A4)[0] - 2.4 * cm
        largeur_colonne = largeur_utile / max(len(apercu.columns), 1)

        table = Table(donnees, repeatRows=1,
                      colWidths=[largeur_colonne] * len(apercu.columns))
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00A86B")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F0F2F6")]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(table)

        # -------- mention de troncature --------
        avertissements = []
        if total_lignes > max_lignes:
            avertissements.append(f"{max_lignes} lignes sur {total_lignes}")
        if total_colonnes > max_colonnes:
            avertissements.append(f"{max_colonnes} colonnes sur {total_colonnes}")
        if avertissements:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                "Apercu limite : " + " et ".join(avertissements)
                + ". Utilisez l'export Excel pour le detail complet.",
                styles["Italic"]))

        doc.build(elements)
        logger.info("PDF genere : %s (%s lignes)", titre, total_lignes)
        return tampon.getvalue()