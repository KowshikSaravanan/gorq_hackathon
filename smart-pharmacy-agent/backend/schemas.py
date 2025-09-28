from pydantic import BaseModel
from datetime import date

class InventoryCreate(BaseModel):
    center_id: str
    drug: str
    stock: float
    avg_daily_demand: float
    lead_time_days: int = 3
    safety_stock: float = 0.0
    expiry_date: date

class InventoryOut(InventoryCreate):
    id: int
    class Config:
        from_attributes = True
