import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base

# Expecting DATABASE_URL like: mysql://user:pass@db:3306/dbname
DATABASE_URL = os.environ.get("DATABASE_URL")

# Convert mysql:// to async driver mysql+aiomysql:// if necessary
if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+aiomysql://", 1)

# Create async engine and sessionmaker
engine = create_async_engine(DATABASE_URL, future=True, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db(retries: int = 10, delay: float = 2.0):
    """
    Create tables at startup (development convenience).
    Retries for a short period to allow the DB container to become ready.
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except Exception as exc:
            last_exc = exc
            if attempt == retries:
                # no more retries, raise the last exception
                raise
            await asyncio.sleep(delay)

def get_session():
    """
    Return an AsyncSession factory. Use as:
        async with get_session() as session:
            ...
    """
    return async_session()