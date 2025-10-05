"""
Integration Test: Redistribution and Routing Workflow 🚚💊

This script validates the full pipeline:
    1. Forecast generation (simple or Groq)
    2. Redistribution logic (detect near-expiry drugs)
    3. Route building and nearest neighbor optimization

Run directly:
    python backend/services/test_features.py
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Tuple, Optional

# Add root dir so "backend" can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Local imports
from backend.services.forecasting import compute_forecast
from backend.services.groq_agent import forecast_with_groq
from backend.services.redistribution import near_expiry_redistribution
from backend.services.routing import nearest_neighbor_route, build_stops_from_moves


def test_redistribution_and_routing(use_groq: bool = False) -> Tuple[pd.DataFrame, Optional[List[str]], float]:
    """
    Test full redistribution + routing workflow.

    Args:
        use_groq (bool): If True, use LLM-based forecasting (Groq); else use simple forecasting.

    Returns:
        Tuple[pd.DataFrame, list, float]:
            - moves_df: suggested redistribution moves
            - route: optimized route list
            - total_dist: total distance in km
    """

    print("\n🚀 Starting test: Redistribution and Routing")
    print(f"🔮 Forecast mode: {'Groq API' if use_groq else 'Compute Forecast'}")

    # ----------------------------
    # Step 1: Load test datasets
    # ----------------------------
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    DATA_DIR = os.path.join(ROOT_DIR, "data")

    data_files = {
        "inventory": os.path.join(DATA_DIR, "test_redistribution_routing.csv"),
        "centers": os.path.join(DATA_DIR, "centers.csv"),
        "demand": os.path.join(DATA_DIR, "demand_signals.csv"),
    }

    for key, path in data_files.items():
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ Missing required file: {path}")
        else:
            print(f"✅ Loaded {key} file: {path}")

    inventory_df = pd.read_csv(data_files["inventory"])
    centers_df = pd.read_csv(data_files["centers"])
    demand_df = pd.read_csv(data_files["demand"])

    if inventory_df.empty or centers_df.empty or demand_df.empty:
        print("⚠️ One or more input files are empty. Exiting early.")
        return pd.DataFrame(), None, 0.0

    # ----------------------------
    # Step 2: Forecast generation
    # ----------------------------
    demand_forecasts: Dict[Tuple[str, str], List[float]] = {}

    print("\n📈 Generating demand forecasts...")
    for (center, drug), group in demand_df.groupby(["center_id", "drug"]):
        hist = group["qty"].tolist()
        if not hist:
            continue

        try:
            if use_groq:
                forecast = forecast_with_groq(hist, horizon=7, drug=drug)
            else:
                forecast = compute_forecast(hist, horizon=7, center_id=center, drug=drug)
        except Exception as e:
            print(f"⚠️ Forecast failed for {center}-{drug}: {e}")
            # fallback to simple moving average
            forecast = [sum(hist[-3:]) / min(3, len(hist))] * 7

        demand_forecasts[(center, drug)] = forecast
        print(f"  ✅ {center}-{drug}: {forecast}")

    # ----------------------------
    # Step 3: Redistribution
    # ----------------------------
    print("\n♻️ Running redistribution logic...")
    moves_df = near_expiry_redistribution(inventory_df, demand_forecasts, horizon=7, expiry_days=30)

    if moves_df.empty:
        print("✅ No redistribution needed — all inventories are balanced or valid.")
        return moves_df, None, 0.0

    print(f"\nSuggested Moves ({len(moves_df)}):")
    print(moves_df.head(10).to_string(index=False))

    # ----------------------------
    # Step 4: Route Optimization
    # ----------------------------
    print("\n🗺️ Building optimized route (Depot = 'C01')...")
    depot, stops = build_stops_from_moves(moves_df, centers_df, "C01")
    route, total_dist = nearest_neighbor_route(depot, stops)

    print(f"🚛 Optimized Route: {route}")
    print(f"📏 Total Distance: {total_dist:.2f} km")

    return moves_df, route, total_dist


if __name__ == "__main__":
    # Run local test without Groq for speed
    print("\n========== LOCAL TEST: Compute Forecast ==========")
    moves, route, dist = test_redistribution_and_routing(use_groq=False)
    print(f"🏁 Completed: {len(moves)} moves | {len(route) if route else 0} stops | {dist:.2f} km")

    # Optional Groq-based test
    print("\n========== LLM TEST: GROQ FORECAST ==========")
    try:
        moves_groq, route_groq, dist_groq = test_redistribution_and_routing(use_groq=True)
        print(f"🏁 Completed (Groq): {len(moves_groq)} moves | {len(route_groq) if route_groq else 0} stops | {dist_groq:.2f} km")
    except Exception as e:
        print(f"⚠️ Groq test skipped: {e}")
