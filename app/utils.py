from fastapi import HTTPException,status, Depends
from passlib.context import CryptContext
import secrets
import hashlib
from sqlalchemy.orm import Session
from . import models
import string
import time
import uuid


pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hashing(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def generate_api_key(prefix: str = "url_") -> str:
    """Generates a secure, 43-character URL-safe string with a prefix."""
    # 32 bytes of randomness creates a highly secure 43-character string
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}{random_part}"

def hash_api_key(api_key: str) -> str:
    """Creates a fast, deterministic hash for direct database lookups."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def get_curr_user(api_key:str, db:Session):
    hashed_api_key = hash_api_key(api_key)
    user = db.query(models.Users).filter(models.Users.api_key == hashed_api_key).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API-Key")

    return user


def generate_short_code(length: int = 6) -> str:
    """Generates a random Base62 string of a given length."""
    # This creates a string of: abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789
    chars = string.ascii_letters + string.digits

    # Pick a random character 6 times and join them together
    return "".join(secrets.choice(chars) for _ in range(length))


def unique_request_id():
    # Current Unix timestamp in milliseconds
    timestamp = int(time.time() * 1000)
    # Generate a random UUID
    unique_id = uuid.uuid4()
    # Combine them
    return f"{timestamp}-{unique_id}"