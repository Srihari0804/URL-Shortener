import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL",
                          os.getenv("TEST_DATABASE_URL") # fallback if production URL is not set
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False, autocommit = False, bind=engine)
Base = declarative_base()

#Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()