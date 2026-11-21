"""
Step 1: collect and assemble block group data.

Outputs (data/processed):
  stations.geojson        public, operating EV stations within 2 miles of the city
  blockgroups.geojson     block groups with income, attached housing share, garage share
  tracts_income.csv       tract median household income
  opa_category_counts.csv OPA category codes with descriptions (check RESIDENTIAL_CODES)
"""
import sys
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import requests

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from config import (RAW, PROCESSED, CRS_M, CRS_LL, ACS_YEAR, STATE_FIPS,
                    COUNTY_FIPS, BUFFER_MAIN_M, BUFFER_WIDE_M,
                    RESIDENTIAL_CODES, census_key)

CARTO = "https://phl.carto.com/api/v2/sql"
ACS_MISSING = -666666666  # Census sentinel for unavailable estimates


# ---------------------------------------------------------------
# Block group and city boundaries
# ---------------------------------------------------------------
def get_blockgroups():
    import pygris
    bg = pygris.block_groups(state=STATE_FIPS, county=COUNTY_FIPS,
                             year=ACS_YEAR, cb=True)
    bg = bg[["GEOID", "ALAND", "geometry"]].to_crs(CRS_M)
    bg["tract_geoid"] = bg["GEOID"].str[:11]
    print(f"block groups: {len(bg)}")
    return bg


# ---------------------------------------------------------------
# Alternative Fuel Stations API
# ---------------------------------------------------------------
def get_stations(city):
    r = requests.get(
        "https://developer.nlr.gov/api/alt-fuel-stations/v1.json",
        params=dict(api_key="DEMO_KEY", fuel_type="ELEC", state="PA,NJ",
                    status="E", access="public", limit="all"),
        timeout=180,
    )
    r.raise_for_status()
    df = pd.DataFrame(r.json()["fuel_stations"])
    keep = ["id", "station_name", "street_address", "city", "state", "zip",
            "ev_network", "ev_level2_evse_num", "ev_dc_fast_num",
            "ev_connector_types", "open_date", "date_last_confirmed",
            "facility_type", "ev_pricing", "latitude", "longitude"]
    df = df[[c for c in keep if c in df.columns]].copy()
    df["ev_connector_types"] = df["ev_connector_types"].astype(str)
    for c in ["ev_level2_evse_num", "ev_dc_fast_num"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
    df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce")

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=CRS_LL
    ).to_crs(CRS_M)

    d = gdf.geometry.distance(city)
    gdf = gdf[d <= BUFFER_WIDE_M].copy()
    gdf["in_city"] = d.loc[gdf.index] == 0
    gdf["in_main_buffer"] = d.loc[gdf.index] <= BUFFER_MAIN_M
    gdf["has_l2"] = gdf["ev_level2_evse_num"] > 0
    gdf["has_dcfc"] = gdf["ev_dc_fast_num"] > 0

    print(f"stations within 2 mi: {len(gdf)} | in city: {gdf.in_city.sum()} | "
          f"within 1 mi: {gdf.in_main_buffer.sum()}")
    print(f"  L2 stations: {gdf.has_l2.sum()} | DCFC stations: {gdf.has_dcfc.sum()} | "
          f"open_date missing: {gdf.open_date.isna().sum()}")
    return gdf


# ---------------------------------------------------------------
# Census ACS 5-year
# ---------------------------------------------------------------
def acs(get, geo_for):
    r = requests.get(
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5",
        params={"get": get, "for": geo_for,
                "in": f"state:{STATE_FIPS} county:{COUNTY_FIPS}",
                "key": census_key()},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    return pd.DataFrame(j[1:], columns=j[0])


def get_acs():
    tr = acs("B19013_001E", "tract:*")
    tr["tract_geoid"] = tr.state + tr.county + tr.tract
    tr["med_income"] = pd.to_numeric(tr["B19013_001E"]).replace(ACS_MISSING, np.nan)
    tr = tr[["tract_geoid", "med_income"]]

    # B25024: units in structure (001 total, 003 one-unit attached)
    # B25044: tenure by vehicles available (003 owner no vehicle, 010 renter no vehicle)
    v = ["B25024_001E", "B25024_003E", "B25044_001E", "B25044_003E", "B25044_010E"]
    bg = acs(",".join(v), "block group:*")
    bg["GEOID"] = bg.state + bg.county + bg.tract + bg["block group"]
    bg[v] = bg[v].apply(pd.to_numeric)
    bg["housing_units"] = bg["B25024_001E"]
    bg["attached_share"] = bg["B25024_003E"] / bg["B25024_001E"].replace(0, np.nan)
    bg["zero_veh_share"] = ((bg["B25044_003E"] + bg["B25044_010E"])
                            / bg["B25044_001E"].replace(0, np.nan))
    bg["households"] = bg["B25044_001E"]
    bg = bg[["GEOID", "housing_units", "households", "attached_share", "zero_veh_share"]]

    print(f"tracts: {len(tr)} (income missing: {tr.med_income.isna().sum()}) | "
          f"block groups: {len(bg)}")
    return tr, bg


# ---------------------------------------------------------------
# OPA property assessments (Carto SQL API): garage share
# ---------------------------------------------------------------
def carto_csv(q):
    r = requests.get(CARTO, params={"q": q, "format": "csv"}, timeout=600)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text), dtype={"category_code": str})


def get_garage_share(bg):
    cats = carto_csv(
        "SELECT category_code, category_code_description, count(*) AS n "
        "FROM opa_properties_public GROUP BY 1, 2 ORDER BY n DESC")
    cats.to_csv(PROCESSED / "opa_category_counts.csv", index=False)
    print("OPA category codes:\n", cats.to_string(index=False))

    codes = ",".join(f"'{c}'" for c in RESIDENTIAL_CODES)
    raw_path = RAW / "opa_residential.csv"
    if raw_path.exists():
        opa = pd.read_csv(raw_path, dtype={"category_code": str})
    else:
        opa = carto_csv(
            "SELECT parcel_number, category_code, garage_spaces, "
            "ST_X(the_geom) AS lng, ST_Y(the_geom) AS lat "
            f"FROM opa_properties_public WHERE category_code IN ({codes})")
        opa.to_csv(raw_path, index=False)
    n_all = len(opa)
    opa = opa.dropna(subset=["lng", "lat"])
    opa["garage_spaces"] = pd.to_numeric(opa["garage_spaces"], errors="coerce")
    print(f"OPA residential: {n_all} | with location: {len(opa)} | "
          f"garage_spaces missing: {opa.garage_spaces.isna().sum()}")

    pts = gpd.GeoDataFrame(
        opa, geometry=gpd.points_from_xy(opa.lng, opa.lat), crs=CRS_LL
    ).to_crs(CRS_M)
    pts = gpd.sjoin(pts, bg[["GEOID", "geometry"]], how="inner", predicate="within")
    pts["has_garage"] = pts["garage_spaces"].fillna(0) > 0

    g = pts.groupby("GEOID").agg(res_parcels=("parcel_number", "size"),
                                 garage_parcels=("has_garage", "sum"))
    g["garage_share"] = g.garage_parcels / g.res_parcels
    print(f"citywide garage share: {g.garage_parcels.sum() / g.res_parcels.sum():.3f}")
    return g.reset_index()


def main():
    bg = get_blockgroups()
    city = bg.unary_union

    st = get_stations(city)
    st.to_file(PROCESSED / "stations.geojson", driver="GeoJSON")

    tr, acs_bg = get_acs()
    tr.to_csv(PROCESSED / "tracts_income.csv", index=False)

    garage = get_garage_share(bg)

    out = (bg.merge(acs_bg, on="GEOID", how="left")
             .merge(tr, on="tract_geoid", how="left")
             .merge(garage, on="GEOID", how="left"))
    # Analysis universe: block groups with housing units and residential parcels
    out["in_universe"] = (out.housing_units > 0) & (out.res_parcels.fillna(0) >= 10)
    print(f"block groups in analysis universe: {out.in_universe.sum()} of {len(out)}")
    out.to_file(PROCESSED / "blockgroups.geojson", driver="GeoJSON")


if __name__ == "__main__":
    main()
