import asyncpg
from .config import DATABASE_URL

db_pool: asyncpg.Pool | None = None

async def connect_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL)
    return db_pool

async def get_db():
    # FastAPI dependency
    if db_pool is None:
        await connect_db()
    return db_pool
