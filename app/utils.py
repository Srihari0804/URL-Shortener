from passlib.context import CryptContext
import secrets
import hashlib

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
