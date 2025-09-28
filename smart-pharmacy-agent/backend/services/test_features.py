import pandas as pd
from .forecasting import simple_forecast
from .groq_agent import forecast_with_groq
from .redistribution import near_expiry_redistribution
from .routing import nearest_neighbor_route, build_stops_from_moves

def test_redistribution_and_routing(use_groq=False):
    # Load test data
    inventory_df = pd.read_csv('data/test_redistribution_routing.csv')
    centers_df = pd.read_csv('data/centers.csv')
    demand_df = pd.read_csv('data/demand_signals.csv')
    
    # Generate forecasts for each (center, drug) pair
    demand_forecasts = {}
    for (center, drug), group in demand_df.groupby(['center_id', 'drug']):
        hist = group['qty'].tolist()
        if use_groq:
            forecast = forecast_with_groq(hist, horizon=7, drug=drug)
        else:
            forecast = simple_forecast(hist, horizon=7)
        demand_forecasts[(center, drug)] = forecast
    
    # Run redistribution
    moves_df = near_expiry_redistribution(inventory_df, demand_forecasts, horizon=7, expiry_days=30)
    print("Suggested Moves:\n", moves_df)
    
    if not moves_df.empty:
        # Build and optimize route (depot C01)
        depot, stops = build_stops_from_moves(moves_df, centers_df, 'C01')
        route, total_dist = nearest_neighbor_route(depot, stops)
        print(f"Optimized Route: {route}, Total Distance: {total_dist:.2f} km")
    else:
        print("No moves suggested - no redistribution needed.")
    
    return moves_df, route if 'route' in locals() else None, total_dist if 'total_dist' in locals() else 0

if __name__ == "__main__":
    # Run test without Groq (fast)
    moves, route, dist = test_redistribution_and_routing(use_groq=False)
    print(f"\nTest completed. Moves: {len(moves)}, Route length: {len(route) if route else 0}, Distance: {dist}")
    
    # Optionally run with Groq for LLM forecasts
    # moves_groq, route_groq, dist_groq = test_redistribution_and_routing(use_groq=True)
