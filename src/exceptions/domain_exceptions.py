"""Exceptions personnalisees du domaine Gestion de Stock."""


class StockAppError(Exception):
    """Classe de base de toutes les exceptions de l application."""

    def __init__(self, message: str = "Erreur applicative", code: str = "ERR_GEN"):
        self.message = message
        self.code = code
        super().__init__(message)

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ConnexionBDError(StockAppError):
    def __init__(self, message="Connexion a la base de donnees impossible."):
        super().__init__(message, "ERR_DB_CONN")


class RequeteBDError(StockAppError):
    def __init__(self, message="Erreur lors de l execution de la requete."):
        super().__init__(message, "ERR_DB_QUERY")


class ProduitIntrouvableError(StockAppError):
    def __init__(self, reference):
        super().__init__(f"Produit introuvable : {reference}", "ERR_PROD_404")


class FournisseurIntrouvableError(StockAppError):
    def __init__(self, identifiant):
        super().__init__(f"Fournisseur introuvable : {identifiant}", "ERR_FOUR_404")


class StockInsuffisantError(StockAppError):
    def __init__(self, produit, disponible, demande):
        super().__init__(
            f"Stock insuffisant pour {produit} : {disponible} disponible(s), "
            f"{demande} demande(s).", "ERR_STOCK_LOW")


class QuantiteInvalideError(StockAppError):
    def __init__(self, quantite):
        super().__init__(f"Quantite invalide : {quantite}", "ERR_QTE")


class DoublonError(StockAppError):
    def __init__(self, champ, valeur):
        super().__init__(f"La valeur {valeur} existe deja pour {champ}.", "ERR_DUPLICATE")


class ValidationError(StockAppError):
    def __init__(self, champ, raison):
        super().__init__(f"Champ {champ} invalide : {raison}", "ERR_VALID")


class AuthentificationError(StockAppError):
    def __init__(self, message="Identifiants incorrects."):
        super().__init__(message, "ERR_AUTH")


class CompteDesactiveError(StockAppError):
    def __init__(self, login):
        super().__init__(f"Le compte {login} est desactive.", "ERR_ACCOUNT_OFF")


class PermissionRefuseeError(StockAppError):
    def __init__(self, role, action):
        super().__init__(f"Le role {role} ne peut pas : {action}", "ERR_PERM")
