from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import hmac
import base64
import json
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-use-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours


# ── Simple password hashing (SHA-256 + HMAC; swap for bcrypt in production) ──

def hash_password(plain: str) -> str:
    salt = os.urandom(16)
    dk = hmac.new(SECRET_KEY.encode(), salt + plain.encode(), hashlib.sha256).digest()
    return base64.b64encode(salt + dk).decode()


def verify_password(plain: str, stored: str) -> bool:
    try:
        raw = base64.b64decode(stored.encode())
        salt, dk = raw[:16], raw[16:]
        check = hmac.new(SECRET_KEY.encode(), salt + plain.encode(), hashlib.sha256).digest()
        return hmac.compare_digest(dk, check)
    except Exception:
        return False


# ── Minimal JWT (no external deps) ──

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = dict(data)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = int(expire.timestamp())
    header = _b64url_encode(json.dumps({"alg": ALGORITHM, "typ": "JWT"}).encode())
    body   = _b64url_encode(json.dumps(payload).encode())
    sig    = _b64url_encode(
        hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{body}.{sig}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        header, body, sig = token.split(".")
        expected = _b64url_encode(
            hmac.new(SECRET_KEY.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64url_decode(body))
        if payload.get("exp", 0) < datetime.now(timezone.utc).timestamp():
            return None
        return payload
    except Exception:
        return None
