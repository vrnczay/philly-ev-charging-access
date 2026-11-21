"""
Step 2: download walking and driving networks with OSMnx.

Networks cover the city plus a 3.5 km buffer so stations in the two-mile
sensitivity buffer sit on the network instead of snapping to the city edge.

Outputs (data/raw, git-ignored because of size):
  walk_buffered.graphml
  drive_buffered.graphml   (edge speeds and travel times added)
"""
import sys
import time
from pathlib import Path

import geopandas as gpd
import osmnx as ox

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from config import RAW, PROCESSED, CACHE, CRS_LL, NETWORK_BUFFER_M

ox.settings.use_cache = True
ox.settings.cache_folder = str(CACHE)
ox.settings.timeout = 900
ox.settings.log_console = False


def study_polygon():
    bg = gpd.read_file(PROCESSED / "blockgroups.geojson")
    poly = gpd.GeoSeries([bg.unary_union.buffer(NETWORK_BUFFER_M)], crs=bg.crs)
    return poly.to_crs(CRS_LL).iloc[0]


def build(kind, poly):
    path = RAW / f"{kind}_buffered.graphml"
    if path.exists():
        print(f"{kind}: exists, skipping ({path.name})")
        return
    t0 = time.time()
    G = ox.graph_from_polygon(poly, network_type=kind)
    if kind == "drive":
        G = ox.add_edge_speeds(G)
        G = ox.add_edge_travel_times(G)
        # keep the largest strongly connected component so every node can reach a charger
        G = ox.utils_graph.get_largest_component(G, strongly=True)
    G = ox.project_graph(G)
    ox.save_graphml(G, path)
    print(f"{kind}: nodes={len(G.nodes)}, edges={len(G.edges)}, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    poly = study_polygon()
    build("walk", poly)
    build("drive", poly)
