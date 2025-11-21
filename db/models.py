#models.py
from sqlalchemy import Column, Integer, String
from db.database import Base

class EmployeeModel(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    job = Column(String(100), nullable=False)
    language = Column(String(100))
    pay = Column(String(100), nullable=False)


