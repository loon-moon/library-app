import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY_ENV = "SECRET_KEY"
SECRET_KEY_FILE = BASE_DIR / ".secret_key"
SESSION_MAX_AGE = 60 * 60 * 24 * 7
SESSION_COOKIE_NAME = "library_session"


def _load_secret_key() -> str:
    env_value = os.getenv(SECRET_KEY_ENV)
    if env_value:
        return env_value

    if SECRET_KEY_FILE.exists():
        value = SECRET_KEY_FILE.read_text(encoding="utf-8").strip()
        if value:
            return value

    value = secrets.token_urlsafe(48)
    SECRET_KEY_FILE.write_text(value, encoding="utf-8")
    return value


SECRET_KEY = _load_secret_key()
