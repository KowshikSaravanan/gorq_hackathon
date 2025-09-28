import pandas as pd
from datetime import datetime, timedelta

def near_expiry_redistribution(inventory_df: pd.DataFrame, demand_forecasts: dict, horizon:int=7, expiry_days:int=30):
    """Suggest moving near-expiry stock to centers with predicted shortfall.
    inventory_df: columns center_id, drug, stock, expiry_date
    demand_forecasts: {(center_id, drug): forecast_array}
    Returns DataFrame: from_center,to_center,drug,qty,reason
    """
    today = pd.Timestamp(datetime.utcnow().date())
    inv = inventory_df.copy()
    inv['expiry_date'] = pd.to_datetime(inv['expiry_date'])
    inv['days_to_expiry'] = (inv['expiry_date'] - today).dt.days
    near = inv[inv['days_to_expiry']<=expiry_days].copy()

    moves = []
    for _, row in near.iterrows():
        key = (row.center_id, row.drug)
        forecast = demand_forecasts.get(key, [0]*horizon)
        need = sum(forecast)  # demand over horizon
        surplus = max(0, row.stock - need)
        if surplus <= 0:
            continue
        # find target centers with deficit
        for (c2, d2), f2 in demand_forecasts.items():
            if d2 != row.drug or c2 == row.center_id: 
                continue
            need2 = sum(f2)
            stock2 = inv[(inv.center_id==c2)&(inv.drug==row.drug)]['stock'].sum()
            deficit = max(0, need2 - stock2)
            if deficit<=0:
                continue
            qty = min(surplus, deficit)
            if qty > 0:
                moves.append({
                    'from_center': row.center_id,
                    'to_center': c2,
                    'drug': row.drug,
                    'qty': round(qty,2),
                    'reason': f'Near expiry in {row.days_to_expiry} days'
                })
                surplus -= qty
                if surplus<=0:
                    break
    return pd.DataFrame(moves)
