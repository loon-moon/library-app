import hashlib

import bcrypt

BCRYPT_MAX_BYTES = 72
BCRYPT_ROUNDS = 12


def _password_bytes(password: str) -> bytes:
    raw = password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_BYTES:
        return hashlib.sha256(raw).hexdigest().encode("ascii")
    return raw


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        _password_bytes(password),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _password_bytes(password),
            password_hash.encode("ascii"),
        )
    except (ValueError, TypeError):
        return False
