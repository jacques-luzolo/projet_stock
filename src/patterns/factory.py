"""
Design Pattern : FACTORY METHOD (Fabrique).

Probleme resolu :
    Le code qui cree des mouvements ne doit pas connaitre toutes les
    classes concretes (Entree, Sortie, Transfert, Ajustement).
    Il demande simplement "cree-moi un mouvement de type X".

Avantage :
    Ajouter un nouveau type de mouvement ne modifie pas le code appelant
    (principe Ouvert/Ferme du SOLID).
"""
from src.exceptions.domain_exceptions import ValidationError
from src.models.mouvement import Ajustement, Entree, Mouvement, Sortie, Transfert
from src.models.produit import Produit, ProduitPerissable
from src.utils.logger import logger


class MouvementFactory:
    """Fabrique centralisee de mouvements de stock."""

    # Table de correspondance : type demande -> classe concrete
    _TYPES = {
        "ENTREE": Entree,
        "SORTIE": Sortie,
        "TRANSFERT": Transfert,
        "AJUSTEMENT": Ajustement,
    }

    @classmethod
    def creer(cls, type_mouvement, **kwargs):
        """
        Instancie le bon type de mouvement.

        Exemple :
            mvt = MouvementFactory.creer("ENTREE", produit_id=1,
                                         quantite=10, utilisateur_id=1,
                                         entrepot_dest_id=1)
        """
        cle = (type_mouvement or "").strip().upper()
        classe = cls._TYPES.get(cle)

        if classe is None:
            raise ValidationError(
                "type de mouvement",
                f"'{type_mouvement}' inconnu. Valeurs possibles : "
                f"{', '.join(cls._TYPES)}"
            )

        mouvement = classe(**kwargs)
        mouvement.valider()
        logger.debug("Mouvement %s cree par la fabrique", cle)
        return mouvement

    @classmethod
    def types_disponibles(cls):
        """Liste des types geres (utile pour un menu deroulant)."""
        return list(cls._TYPES.keys())

    @classmethod
    def enregistrer_type(cls, nom, classe):
        """
        Ajoute dynamiquement un nouveau type de mouvement
        sans modifier le code de la fabrique (extensibilite).
        """
        if not issubclass(classe, Mouvement):
            raise ValidationError("classe", "doit heriter de Mouvement")
        cls._TYPES[nom.upper()] = classe
        logger.info("Nouveau type de mouvement enregistre : %s", nom)


class ProduitFactory:
    """Fabrique de produits : choisit Produit ou ProduitPerissable."""

    @staticmethod
    def creer(donnees):
        """
        Construit le bon type de produit a partir d'un dictionnaire
        (typiquement une ligne lue dans la base de donnees).
        """
        perissable = bool(donnees.get("perissable"))

        commun = {
            "prix_achat": donnees.get("prix_achat", 0),
            "prix_vente": donnees.get("prix_vente", 0),
            "seuil_min": donnees.get("seuil_min", 0),
            "seuil_max": donnees.get("seuil_max", 0),
            "unite": donnees.get("unite", "pcs"),
            "categorie_id": donnees.get("categorie_id"),
            "fournisseur_id": donnees.get("fournisseur_id"),
            "description": donnees.get("description", ""),
            "actif": bool(donnees.get("actif", True)),
            "id_": donnees.get("id"),
            "cree_le": donnees.get("cree_le"),
        }

        if perissable:
            produit = ProduitPerissable(
                donnees["reference"],
                donnees["designation"],
                date_peremption=donnees.get("date_peremption"),
                **commun,
            )
        else:
            produit = Produit(donnees["reference"], donnees["designation"], **commun)

        produit.quantite_totale = donnees.get("quantite_totale", 0)
        return produit