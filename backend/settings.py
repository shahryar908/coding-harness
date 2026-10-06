import os
import warnings

from dotenv import load_dotenv

load_dotenv()

_DEV_JWT_SECRET = "dev-insecure-change-me"


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
JWT_SECRET = os.getenv("JWT_SECRET", _DEV_JWT_SECRET)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
CORS_ORIGINS = _csv(os.getenv("CORS_ORIGINS", "*"))

if JWT_SECRET == _DEV_JWT_SECRET:
    if ENVIRONMENT == "production":
        raise RuntimeError("JWT_SECRET must be set in production")
    warnings.warn("JWT_SECRET not set; using an insecure development secret", stacklevel=1)
