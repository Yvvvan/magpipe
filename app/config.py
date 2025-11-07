import os
from dotenv import load_dotenv

load_dotenv()  # load .env if present

API_KEY = os.getenv("API_KEY", "dev-secret")

POSTGRES_USER = os.getenv("POSTGRES_USER", "maguser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "magpass")
POSTGRES_DB = os.getenv("POSTGRES_DB", "magdb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
