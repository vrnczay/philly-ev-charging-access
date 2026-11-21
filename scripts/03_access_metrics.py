"""
Step 3: network access metrics for each block group.

Walk (Level 2):
  walk_l2_m          walking distance, centroid to nearest L2 station (1-mile station buffer)
  walk_l2_wide_m     same, with the 2-mile station buffer (boundary sensitivity)
  l2_ports_400/800/1200  L2 ports within each walking distance
Drive (DC fast):
  drive_dcfc_m       driving distance, centroid to nearest DCFC station
  drive_dcfc_min     free-flow driving time in minutes

Distances include the straight-line snap from centroid to its nearest network node.

Output: data/processed/bg_access.geojson
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, PROCESSED, WALK_CUTOFFS_M


def snap(G, gdf):
    """Nearest node ids and snap distance (m) for point geometries."""
    nodes, dist = ox.distance.nearest_nodes(G, gdf.geometry.x, gdf.geometry.y,
                                            return_dist=True)
    return np.asarray(nodes), np.asarray(dist)


def snap_stations(G, gdf, label, max_snap=300):
    """Snap stations; drop any farther than max_snap m from the network."""
    nodes, dist = snap(G, gdf)
    ok = dist <= max_snap
    if (~ok).any():
        print(f"  {label}: dropped {(~ok).sum()} stations more than {max_snap} m from the network")
    return gdf[ok], nodes[ok], dist[ok]


def nearest_distance(G, source_nodes, target_nodes, weight, reverse=False):
    """Network distance from each target node to the closest source node."""
    H = G.reverse(copy=False) if reverse else G
    d = nx.multi_source_dijkstra_path_length(H, set(source_nodes), weight=weight)
    return np.array([d.get(n, np.nan) for n in target_nodes])


def ports_within(G, st_nodes, ports, bg_nodes, cutoffs):
    """Sum of ports at stations reachable within each walking cutoff."""
    per_node = pd.Series(ports, index=st_nodes).groupby(level=0).sum()
    bg_set = set(bg_nodes)
    totals = {c: pd.Series(0.0, index=list(bg_set)) for c in cutoffs}
    for node, p in per_node.items():
        reach = nx.single_source_dijkstra_path_length(G, node, cutoff=max(cutoffs),
                                                      weight="length")
        hit = {n: d for n, d in reach.items() if n in bg_set}
        for c in cutoffs:
            idx = [n for n, d in hit.items() if d <= c]
            totals[c].loc[idx] += p
    return {c: totals[c].reindex(bg_nodes).to_numpy() for c in cutoffs}


def main():
    bg = gpd.read_file(PROCESSED / "blockgroups.geojson")
    st = gpd.read_file(PROCESSED / "stations.geojson")

    # ---------------- walking: Level 2 ----------------
    t0 = time.time()
    Gw = ox.load_graphml(RAW / "walk_buffered.graphml")
    crs = Gw.graph["crs"]
    bg = bg.to_crs(crs)
    st = st.to_crs(crs)
    cent = gpd.GeoDataFrame(geometry=bg.geometry.centroid, crs=crs)
    bg_w, bg_w_snap = snap(Gw, cent)
    print(f"walk graph loaded: {len(Gw.nodes)} nodes, {time.time() - t0:.0f}s")

    l2_main = st[st.has_l2 & st.in_main_buffer]
    l2_wide = st[st.has_l2]
    l2_main, n_main, s_main = snap_stations(Gw, l2_main, "L2 main")
    l2_wide, n_wide, _ = snap_stations(Gw, l2_wide, "L2 wide")
    print(f"L2 stations: main={len(l2_main)}, wide={len(l2_wide)}, "
          f"median station snap={np.median(s_main):.0f} m")

    bg["walk_l2_m"] = nearest_distance(Gw, n_main, bg_w, "length") + bg_w_snap
    bg["walk_l2_wide_m"] = nearest_distance(Gw, n_wide, bg_w, "length") + bg_w_snap
    bg["centroid_snap_walk_m"] = bg_w_snap

    ports = ports_within(Gw, n_main, l2_main.ev_level2_evse_num.to_numpy(),
                         bg_w, WALK_CUTOFFS_M)
    for c, v in ports.items():
        bg[f"l2_ports_{c}"] = v
    print(f"walk metrics done, {time.time() - t0:.0f}s")
    del Gw

    # ---------------- driving: DC fast ----------------
    t0 = time.time()
    Gd = ox.load_graphml(RAW / "drive_buffered.graphml")
    bg_d, bg_d_snap = snap(Gd, cent.to_crs(Gd.graph["crs"]))
    dc = st[st.has_dcfc & st.in_main_buffer].to_crs(Gd.graph["crs"])
    dc, n_dc, _ = snap_stations(Gd, dc, "DCFC")
    print(f"DCFC stations: {len(dc)}")

    # reverse graph: distance from each block group TO the nearest charger on one-way streets
    bg["drive_dcfc_m"] = nearest_distance(Gd, n_dc, bg_d, "length", reverse=True) + bg_d_snap
    bg["drive_dcfc_min"] = nearest_distance(Gd, n_dc, bg_d, "travel_time", reverse=True) / 60
    print(f"drive metrics done, {time.time() - t0:.0f}s")

    out = bg.to_crs(4326)
    out.to_file(PROCESSED / "bg_access.geojson", driver="GeoJSON")

    u = out[out.in_universe]
    print("\nSummary (analysis universe):")
    print(u[["walk_l2_m", "walk_l2_wide_m", "l2_ports_800",
             "drive_dcfc_m", "drive_dcfc_min"]].describe().round(1).to_string())
    diff = (u.walk_l2_m - u.walk_l2_wide_m)
    print(f"\nBoundary check: {(diff > 1).sum()} block groups get closer with the 2-mile buffer "
          f"(max change {diff.max():.0f} m)")


if __name__ == "__main__":
    main()
