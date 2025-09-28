import math

def z_for_service(service_level: float=0.95):
    # approximate z-scores for common service levels
    mapping = {0.90:1.28, 0.95:1.65, 0.98:2.05, 0.99:2.33}
    return mapping.get(round(service_level,2), 1.65)

def reorder_point(avg_daily_demand: float, lead_time_days:int, demand_std: float=None, service_level: float=0.95, safety_stock: float=0.0):
    demand_std = demand_std if demand_std is not None else 0.25*avg_daily_demand
    z = z_for_service(service_level)
    ss = z * demand_std * math.sqrt(max(1, lead_time_days))
    return max(0.0, avg_daily_demand*lead_time_days + ss + safety_stock)

def reorder_suggestion(stock: float, r_point: float, order_multiple:int=1, max_cap: float=None):
    gap = r_point - stock
    if gap <= 0:
        return 0
    qty = math.ceil(gap / order_multiple) * order_multiple
    if max_cap is not None:
        qty = min(qty, int(max_cap))
    return qty
