from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=True,  # Set to False in production
    )
    # logger.info("Database engine created successfully.")
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
        # logger.info("Database session started.")
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.info("Database session closed.")


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database: {e}")
        raise


def test_db_connection():
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        logger.info("Database connection test successful.")
    except SQLAlchemyError as e:
        logger.error(f"Database connection test failed: {e}")
        raise


if __name__ == "__main__":
    init_db()
    test_db_connection()
