#database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL,echo=True,future=True)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()



