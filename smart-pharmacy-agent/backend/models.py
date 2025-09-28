from sqlalchemy import Column, Integer, String, Float, Date, UniqueConstraint
from .db import Base

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    center_id = Column(String, index=True)
    drug = Column(String, index=True)
    stock = Column(Float)
    avg_daily_demand = Column(Float)
    lead_time_days = Column(Integer, default=3)
    safety_stock = Column(Float, default=0.0)
    expiry_date = Column(Date)

    __table_args__ = (UniqueConstraint('center_id','drug', name='uix_center_drug'),)
