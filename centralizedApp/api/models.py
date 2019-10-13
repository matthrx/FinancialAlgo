from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy import Float
from  sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Position(Base):
    __tablename__ = "position"

    id = Column(Integer, primary_key=True)
    position_type = Column(String)
    market = Column(String(6))
    stepin_market = Column(DateTime)
    stepout_market = Column(DateTime, default= None)
    stepin_value = Column(Float(precision='3,8'))
    result_percent = Column(Float(precision='2,4'))
