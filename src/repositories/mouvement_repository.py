"""Depot d'acces aux mouvements de stock, aux stocks et aux alertes."""
from src.patterns.factory import MouvementFactory
from src.repositories.base_repository import BaseRepository
from src.utils.logger import logger


class MouvementRepository(BaseRepository):
    """CRUD et historique des mouvements."""

    TABLE = "mouvements"

    def vers_entite(self, ligne):
        return MouvementFactory.creer(
            ligne["type_mouvement"],
            produit_id=ligne["produit_id"],
            quantite=ligne["quantite"],
            utilisateur_id=ligne["utilisateur_id"],
            entrepot_source_id=ligne.get("entrepot_source_id"),
            entrepot_dest_id=ligne.get("entrepot_dest_id"),
            prix_unitaire=float(ligne.get("prix_unitaire") or 0),
            motif=ligne.get("motif") or "",
            date_mouvement=ligne.get("date_mouvement"),
            id_=ligne["id"],
        )

    def historique(self, produit_id=None, type_mouvement=None, limite=100):
        """Historique enrichi (jointures produits / utilisateurs / entrepots)."""
        sql = """
            SELECT m.id, m.type_mouvement, m.quantite, m.prix_unitaire,
                   m.motif, m.date_mouvement,
                   p.reference, p.designation,
                   u.login AS utilisateur,
                   es.nom AS entrepot_source, ed.nom AS entrepot_dest,
                   (m.quantite * m.prix_unitaire) AS montant
            FROM mouvements m
            JOIN produits p       ON p.id = m.produit_id
            JOIN utilisateurs u   ON u.id = m.utilisateur_id
            LEFT JOIN entrepots es ON es.id = m.entrepot_source_id
            LEFT JOIN entrepots ed ON ed.id = m.entrepot_dest_id
            WHERE 1 = 1
        """
        params = []
        if produit_id:
            sql += " AND m.produit_id = ?"
            params.append(produit_id)
        if type_mouvement:
            sql += " AND m.type_mouvement = ?"
            params.append(type_mouvement)
        sql += " ORDER BY m.date_mouvement DESC LIMIT ?"
        params.append(int(limite))

        with self.db.curseur() as cur:
            cur.execute(sql, tuple(params))
            return [dict(l) for l in cur.fetchall()]

    def enregistrer(self, mouvement):
        """Insere un mouvement valide."""
        mouvement.valider()
        donnees = mouvement.to_dict()
        for cle in ("id", "montant_total"):
            donnees.pop(cle, None)
        mouvement.id = self._inserer(donnees)
        logger.info("Mouvement enregistre : %s", mouvement.libelle())
        return mouvement

    def statistiques_par_type(self, jours=30):
        with self.db.curseur() as cur:
            cur.execute("""
                SELECT type_mouvement,
                       COUNT(*) AS nb,
                       SUM(quantite) AS total_quantite,
                       SUM(quantite * prix_unitaire) AS montant
                FROM mouvements
                WHERE date_mouvement >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
                GROUP BY type_mouvement
            """, (jours,))
            return [dict(l) for l in cur.fetchall()]

    def evolution_journaliere(self, jours=30):
        """Serie temporelle pour les graphiques."""
        with self.db.curseur() as cur:
            cur.execute("""
                SELECT DATE(date_mouvement) AS jour, type_mouvement,
                       SUM(quantite) AS quantite
                FROM mouvements
                WHERE date_mouvement >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
                GROUP BY jour, type_mouvement ORDER BY jour
            """, (jours,))
            return [dict(l) for l in cur.fetchall()]


class StockRepository(BaseRepository):
    """Gestion des quantites par produit et par entrepot."""

    TABLE = "stocks"

    def vers_entite(self, ligne):
        return dict(ligne)

    def quantite(self, produit_id, entrepot_id):
        with self.db.curseur() as cur:
            cur.execute("SELECT quantite FROM stocks "
                        "WHERE produit_id = ? AND entrepot_id = ?",
                        (produit_id, entrepot_id))
            ligne = cur.fetchone()
            return ligne["quantite"] if ligne else 0

    def quantite_totale(self, produit_id):
        with self.db.curseur() as cur:
            cur.execute("SELECT COALESCE(SUM(quantite),0) AS q FROM stocks "
                        "WHERE produit_id = ?", (produit_id,))
            return cur.fetchone()["q"]

    def definir(self, produit_id, entrepot_id, quantite):
        """UPSERT : cree ou met a jour la ligne de stock."""
        with self.db.curseur(commit=True) as cur:
            cur.execute("""
                INSERT INTO stocks (produit_id, entrepot_id, quantite)
                VALUES (?, ?, ?)
                ON DUPLICATE KEY UPDATE quantite = VALUES(quantite)
            """, (produit_id, entrepot_id, max(0, int(quantite))))
        return True

    def detail_produit(self, produit_id):
        """Repartition d'un produit entre les entrepots."""
        with self.db.curseur() as cur:
            cur.execute("""
                SELECT e.nom AS entrepot, e.localisation, s.quantite, s.maj_le
                FROM stocks s JOIN entrepots e ON e.id = s.entrepot_id
                WHERE s.produit_id = ? ORDER BY s.quantite DESC
            """, (produit_id,))
            return [dict(l) for l in cur.fetchall()]


class AlerteRepository(BaseRepository):
    """Gestion des alertes de stock."""

    TABLE = "alertes"

    def vers_entite(self, ligne):
        return dict(ligne)

    def lister_actives(self, niveau=None):
        sql = """SELECT a.*, p.reference, p.designation
                 FROM alertes a JOIN produits p ON p.id = a.produit_id
                 WHERE a.traitee = 0"""
        params = []
        if niveau:
            sql += " AND a.niveau = ?"
            params.append(niveau)
        sql += " ORDER BY FIELD(a.niveau,'CRITIQUE','WARNING','INFO'), a.cree_le DESC"

        with self.db.curseur() as cur:
            cur.execute(sql, tuple(params))
            return [dict(l) for l in cur.fetchall()]

    def creer(self, type_alerte, produit_id, message, niveau="WARNING"):
        """Evite les doublons d'alertes non traitees."""
        with self.db.curseur(commit=True) as cur:
            cur.execute("""SELECT id FROM alertes
                           WHERE produit_id = ? AND type_alerte = ? AND traitee = 0""",
                        (produit_id, type_alerte))
            if cur.fetchone():
                return None
            cur.execute("""INSERT INTO alertes
                           (type_alerte, produit_id, message, niveau)
                           VALUES (?,?,?,?)""",
                        (type_alerte, produit_id, message, niveau))
            return cur.lastrowid

    def marquer_traitee(self, alerte_id):
        return self._mettre_a_jour(alerte_id, {"traitee": 1})

    def compter_actives(self):
        with self.db.curseur() as cur:
            cur.execute("""SELECT niveau, COUNT(*) AS n FROM alertes
                           WHERE traitee = 0 GROUP BY niveau""")
            return {l["niveau"]: l["n"] for l in cur.fetchall()}