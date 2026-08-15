"""Utilitaires de securite : hachage de mots de passe et validations."""
import re

import bcrypt

from src.exceptions.domain_exceptions import ValidationError

_ROUNDS = 12


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Retourne le hash bcrypt (sale) d un mot de passe en clair."""
    if not mot_de_passe:
        raise ValidationError("mot de passe", "ne peut pas etre vide")
    return bcrypt.hashpw(mot_de_passe.encode("utf-8"), bcrypt.gensalt(_ROUNDS)).decode()


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    """Compare un mot de passe en clair avec son hash bcrypt."""
    try:
        return bcrypt.checkpw(mot_de_passe.encode("utf-8"), hash_stocke.encode("utf-8"))
    except (ValueError, TypeError, AttributeError):
        return False


def valider_force_mot_de_passe(mdp: str) -> None:
    """Leve ValidationError si le mot de passe est trop faible."""
    if len(mdp) < 8:
        raise ValidationError("mot de passe", "8 caracteres minimum")
    if not re.search(r"[A-Z]", mdp):
        raise ValidationError("mot de passe", "au moins une majuscule")
    if not re.search(r"[a-z]", mdp):
        raise ValidationError("mot de passe", "au moins une minuscule")
    if not re.search(r"\d", mdp):
        raise ValidationError("mot de passe", "au moins un chiffre")


def valider_email(email: str) -> None:
    """Verifie le format d une adresse e-mail."""
    if not re.match(r"^[\w\.\-\+]+@[\w\-]+\.[a-zA-Z]{2,}$", email or ""):
        raise ValidationError("email", "format invalide")


def nettoyer_texte(texte: str, longueur_max: int = 255) -> str:
    """Nettoie une saisie utilisateur."""
    return "" if texte is None else texte.strip()[:longueur_max]
