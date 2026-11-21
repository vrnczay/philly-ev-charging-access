"""Helpers shared by the analysis notebooks."""
import geopandas as gpd
import numpy as np
import pandas as pd

from config import PROCESSED


def load_bg(universe_only=True):
    """Block groups with access metrics and median-split groups."""
    bg = gpd.read_file(PROCESSED / "bg_access.geojson")
    if universe_only:
        bg = bg[bg.in_universe].copy()

    inc_med = bg.med_income.median()
    gar_med = bg.garage_share.median()
    att_med = bg.attached_share.median()
    bg["income_grp"] = np.where(bg.med_income >= inc_med, "Higher income", "Lower income")
    bg.loc[bg.med_income.isna(), "income_grp"] = np.nan
    bg["garage_grp"] = np.where(bg.garage_share >= gar_med, "More garages", "Few garages")
    bg["attached_grp"] = np.where(bg.attached_share >= att_med, "Mostly attached", "Less attached")
    bg["group"] = bg.garage_grp + " / " + bg.income_grp
    bg.attrs["medians"] = dict(income=inc_med, garage=gar_med, attached=att_med)
    return bg


def load_stations():
    st = gpd.read_file(PROCESSED / "stations.geojson")
    st["open_date"] = pd.to_datetime(st["open_date"], errors="coerce")
    st["open_year"] = st.open_date.dt.year
    return st


def group_summary(df, by, cols=("walk_l2_m", "l2_ports_800", "drive_dcfc_min")):
    """Median of access metrics and block group count per group."""
    g = df.groupby(by)
    out = g[list(cols)].median().round(1)
    out = out.rename(columns={c: f"{c} (median)" for c in cols})
    out.insert(0, "n_blockgroups", g.size())
    out["share with L2 port within 800 m"] = g["l2_ports_800"].apply(lambda s: (s > 0).mean()).round(3)
    return out
