import base64
import glob
import json
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_VERIFIER_PLAINTEXT = b"finarix-v1"


def _auth_path(data_dir: str) -> str:
    return os.path.join(data_dir, ".auth")


def is_configured(data_dir: str) -> bool:
    return os.path.exists(_auth_path(data_dir))


def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def setup_password(password: str, data_dir: str) -> bytes:
    """First-time setup: create salt + verifier, return derived key."""
    os.makedirs(data_dir, exist_ok=True)
    salt = os.urandom(16)
    key = _derive_key(password, salt)
    verifier = Fernet(key).encrypt(_VERIFIER_PLAINTEXT)
    config = {
        "salt": base64.b64encode(salt).decode(),
        "verifier": base64.b64encode(verifier).decode(),
    }
    with open(_auth_path(data_dir), "w", encoding="utf-8") as f:
        json.dump(config, f)
    return key


def verify_password(password: str, data_dir: str):
    """Returns the derived key if password is correct, None otherwise."""
    try:
        with open(_auth_path(data_dir), encoding="utf-8") as f:
            config = json.load(f)
        salt     = base64.b64decode(config["salt"])
        verifier = base64.b64decode(config["verifier"])
        key      = _derive_key(password, salt)
        Fernet(key).decrypt(verifier)
        return key
    except (InvalidToken, Exception):
        return None


def migrate_existing_files(key: bytes, data_dir: str) -> None:
    """Encrypt any plaintext JSON data files left from before encryption was added."""
    fernet = Fernet(key)
    for path in glob.glob(os.path.join(data_dir, "*.json")):
        with open(path, "rb") as f:
            raw = f.read()
        try:
            fernet.decrypt(raw)
            continue  # already encrypted
        except InvalidToken:
            pass
        try:
            json.loads(raw)  # only migrate valid JSON
        except Exception:
            continue
        with open(path, "wb") as f:
            f.write(fernet.encrypt(raw))
