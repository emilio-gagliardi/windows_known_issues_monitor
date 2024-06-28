from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

try:
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,  # Set to False in production
    )
    logger.info("Async database engine created successfully.")
except Exception as e:
    logger.error(f"Error creating async database engine: {e}")
    raise

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            logger.info("Async database session started.")
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.info("Async database session closed.")


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def test_db_connection():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        logger.info("Async database connection test successful.")
    except SQLAlchemyError as e:
        logger.error(f"Async database connection test failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
    asyncio.run(test_db_connection())
