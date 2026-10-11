import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_database_engine():
    # Attempt MySQL first
    mysql_url = settings.mysql_url
    try:
        engine = create_engine(
            mysql_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        # Test connection
        with engine.connect() as conn:
            logger.info("Successfully connected to MySQL Database (%s)", settings.MYSQL_DB)
            return engine, "mysql"
    except Exception as e:
        logger.warning("Could not connect to MySQL Database at %s:%s. Error: %s", 
                       settings.MYSQL_HOST, settings.MYSQL_PORT, str(e))
        if settings.ENABLE_SQLITE_FALLBACK:
            logger.info("Falling back to SQLite database at %s", settings.SQLITE_DB_PATH)
            sqlite_url = settings.sqlite_url
            engine = create_engine(
                sqlite_url,
                connect_args={"check_same_thread": False},
                echo=False
            )
            return engine, "sqlite"
        else:
            raise e

engine, DB_TYPE = get_database_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
