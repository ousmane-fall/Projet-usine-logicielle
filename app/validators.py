"""Validateurs d'entrées simples mais robustes.

Règles :
- email : RFC-light (local@domain.tld), longueur <= 254, pas d'espaces,
  domaine avec au moins un point, TLD >= 2 caractères.
- username : 3 à 32 caractères, lettres/chiffres/underscore/tiret,
  doit commencer par une lettre, pas de tiret ou underscore consécutifs.
"""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(
    r"^(?P<local>[A-Za-z0-9._%+-]{1,64})@"
    r"(?P<domain>[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,62}[A-Za-z0-9])?)+)$"
)
_USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{2,31}$")


class ValidationError(ValueError):
    """Erreur de validation d'entrée."""


def validate_email(email: object) -> str:
    if not isinstance(email, str):
        raise ValidationError("email doit être une chaîne")
    value = email.strip()
    if not value:
        raise ValidationError("email vide")
    if len(value) > 254:
        raise ValidationError("email trop long")
    if any(c.isspace() for c in value):
        raise ValidationError("email contient des espaces")
    match = _EMAIL_RE.match(value)
    if not match:
        raise ValidationError("format email invalide")
    tld = value.rsplit(".", 1)[-1]
    if len(tld) < 2:
        raise ValidationError("TLD invalide")
    return value.lower()


def validate_username(username: object) -> str:
    if not isinstance(username, str):
        raise ValidationError("username doit être une chaîne")
    value = username.strip()
    if not _USERNAME_RE.match(value):
        raise ValidationError(
            "username invalide (3-32 caractères, commence par une lettre, "
            "lettres/chiffres/_/- uniquement)"
        )
    if "--" in value or "__" in value or "-_" in value or "_-" in value:
        raise ValidationError("username: tirets ou underscores consécutifs interdits")
    return value
