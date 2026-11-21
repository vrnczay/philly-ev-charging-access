"""Shared paths and parameters for the Philadelphia EV charging access project."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
CACHE = DATA / "cache"           # OSMnx download cache
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
LOGS = OUTPUTS / "logs"
for p in (RAW, PROCESSED, CACHE, FIGURES, LOGS):
    p.mkdir(parents=True, exist_ok=True)

# Projected CRS in meters (UTM zone 18N)
CRS_M = 32618
CRS_LL = 4326

ACS_YEAR = 2023
STATE_FIPS = "42"
COUNTY_FIPS = "101"

# Station inventory buffers around the city boundary (meters)
BUFFER_MAIN_M = 1609      # one mile, main analysis
BUFFER_WIDE_M = 3219      # two miles, boundary sensitivity check
NETWORK_BUFFER_M = 3500   # networks extend past the widest station buffer

# Walking thresholds for counting nearby Level 2 ports (meters)
WALK_CUTOFFS_M = [400, 800, 1200]

# OPA category codes treated as residential.
# 01_collect_data.py prints every code with its description: confirm before final run.
RESIDENTIAL_CODES = ["1", "2"]


def census_key() -> str:
    return (ROOT / "census_key.txt").read_text().strip()
