from haversine import haversine
import pandas as pd

def nearest_neighbor_route(depot, stops):
    """depot: (lat,lon); stops: list of (id, lat, lon)
    Returns order of stop ids and total distance (km).
    """
    remaining = stops[:]
    route = []
    dist = 0.0
    curr = depot
    while remaining:
        best_i, best_d = None, float('inf')
        for i,(sid,lat,lon) in enumerate(remaining):
            d = haversine(curr, (lat,lon))
            if d < best_d:
                best_d, best_i = d, i
        sid, lat, lon = remaining.pop(best_i)
        route.append(sid)
        dist += best_d
        curr = (lat,lon)
    # return to depot
    dist += haversine(curr, depot)
    return route, dist

def build_stops_from_moves(moves_df: pd.DataFrame, centers_df: pd.DataFrame, depot_center_id:str):
    ids = set(moves_df['to_center'].tolist())
    ids.add(depot_center_id)
    locs = centers_df[centers_df.center_id.isin(ids)].set_index('center_id')[['lat','lon']].to_dict('index')
    depot = (locs[depot_center_id]['lat'], locs[depot_center_id]['lon'])
    stops = [(cid, locs[cid]['lat'], locs[cid]['lon']) for cid in ids if cid!=depot_center_id]
    return depot, stops
