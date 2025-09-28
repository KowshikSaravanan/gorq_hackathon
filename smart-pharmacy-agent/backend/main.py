from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .db import Base, engine, get_db
from .models import Inventory
from .schemas import InventoryCreate, InventoryOut
from .services.forecasting import compute_forecast
from .services.reorder import reorder_point, reorder_suggestion
from .services.redistribution import near_expiry_redistribution
from .services.groq_agent import forecast_with_groq

import pandas as pd

app = FastAPI(title="Smart Pharmacy Inventory Agent")

Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/inventory", response_model=InventoryOut)
def upsert_inventory(item: InventoryCreate, db: Session = Depends(get_db)):
    obj = db.query(Inventory).filter_by(center_id=item.center_id, drug=item.drug).first()
    if obj:
        for f,v in item.model_dump().items():
            setattr(obj, f, v)
    else:
        obj = Inventory(**item.model_dump())
        db.add(obj)
    db.commit(); db.refresh(obj)
    return obj

@app.get("/reorder")
def reorder(center_id:str, drug:str, demand_std: float|None=None, service_level: float=0.95):
    db = next(get_db())
    inv = db.query(Inventory).filter_by(center_id=center_id, drug=drug).first()
    if not inv:
        return {"error":"not found"}
    rpoint = reorder_point(inv.avg_daily_demand, inv.lead_time_days, demand_std, service_level, inv.safety_stock)
    qty = reorder_suggestion(inv.stock, rpoint, order_multiple=1)
    return {"center_id":center_id, "drug":drug, "reorder_point":rpoint, "suggest_order_qty":qty}

@app.post("/redistribute")
def redistribute():
    db = next(get_db())
    rows = db.query(Inventory).all()
    inv_df = pd.DataFrame([{
        'center_id': r.center_id, 'drug': r.drug, 'stock': r.stock, 'expiry_date': r.expiry_date
    } for r in rows])
    # fake forecasts: use avg_daily_demand * 7
    demand = { (r.center_id, r.drug): [r.avg_daily_demand]*7 for r in rows }
    moves = near_expiry_redistribution(inv_df, demand, horizon=7, expiry_days=30)
    return moves.to_dict(orient='records')

@app.get("/forecast_groq")
def forecast_groq(center_id: str, drug: str, horizon: int = 7):
    import pandas as pd
    db = next(get_db())
    # Build simple history from Inventory avg_daily_demand * 1 for last 14 days as a fallback
    rows = db.query(Inventory).filter_by(center_id=center_id, drug=drug).all()
    if not rows:
        history = [0]*14
    else:
        history = [r.avg_daily_demand for r in rows][:14]
    fc = forecast_with_groq(history=history, horizon=horizon, drug=drug)
    return {"center_id": center_id, "drug": drug, "forecast": fc}
