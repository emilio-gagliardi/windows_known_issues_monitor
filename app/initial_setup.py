import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from database import SQLALCHEMY_DATABASE_URL, Base, AsyncSessionLocal
from models import URL as URLModel
from schemas import URLCreate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)


# Function to create tables
async def create_tables():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise


# Function to add a URL
async def add_url(url: str):
    try:
        url_data = URLCreate(url=url)
        async with AsyncSessionLocal() as session:
            new_url = URLModel(url=url_data.url)
            session.add(new_url)
            await session.commit()
        logger.info(f"Added URL: {url}")
    except SQLAlchemyError as e:
        logger.error(f"Error adding URL {url}: {e}")
        raise


# Main function to set up the database
async def setup_database():
    try:
        # Create tables
        await create_tables()

        # Add some initial URLs (modify as needed)
        urls_to_add = [
            "https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-23H2#known-issues",
            "https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-22H2#known-issues",
            "https://learn.microsoft.com/en-us/windows/release-health/status-windows-11-21H2#known-issues",
            "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-22H2#known-issues",
            "https://learn.microsoft.com/en-us/windows/release-health/status-windows-10-21H2#known-issues",
            "https://learn.microsoft.com/en-us/windows/release-health/status-windows-server-2022#known-issues",
        ]

        for url in urls_to_add:
            await add_url(url)

        logger.info("Database setup complete!")
    except Exception as e:
        logger.error(f"Error during database setup: {e}")
        raise


# Run the setup
if __name__ == "__main__":
    asyncio.run(setup_database())
