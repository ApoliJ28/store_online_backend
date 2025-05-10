from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import dotenv_values

config = dotenv_values(".env")
SQLALCHEMY_DATABASE_URL = config['DATABASE_URL']

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit= False, autoflush= False, bind= engine)

Base = declarative_base()
