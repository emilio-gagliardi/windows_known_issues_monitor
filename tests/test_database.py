from app.database import get_db, init_db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session


class TestDatabase:
    def test_get_db(self):
        """
        Test the get_db function to ensure it returns an instance of Session from SQLAlchemy ORM.

        Returns:
            None
        """
        with get_db() as db:
            assert isinstance(db, Session)

    def test_init_and_test_db_connection(self):
        """
        Test the initialization of the database and test the database connection.

        Requires development

        Parameters:
            None

        Returns:
            None
        """
