import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from chalicelib.src.modules.infrastructure.dto import Base

LOGGER = logging.getLogger('abcall-pqrs-events-microservice')

db_session = None
engine = None

def init_db(migrate=False):
    global db_session
    global engine

    environment = os.getenv('ENVIRONMENT', 'local')

    if environment == 'production':
        db_url = os.getenv('DATABASE_URL', '')
    else:
        db_url = "postgresql://myuser:mypassword@localhost:5432/mydb"

    if db_url:
        if engine is None or db_session is None:
            LOGGER.info(f"Connecting to database at {db_url}")
            try:
                engine = create_engine(db_url)
                Session = sessionmaker(bind=engine)
                db_session = Session()
                LOGGER.info("Database connection established.")
                if migrate:
                    import chalicelib.src.modules.infrastructure.dto
                    Base.metadata.create_all(engine)
                    LOGGER.info("Database migrated.")
            except Exception as e:
                LOGGER.error(f"Error establishing database connection: {e}")
                raise e
    else:
        LOGGER.error("DATABASE_URL is not set in environment variables.")
        raise ValueError("DATABASE_URL is not set in environment variables.")

    return db_session