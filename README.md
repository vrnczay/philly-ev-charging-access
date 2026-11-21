# Plugged In or Left Out? Public EV Charging Access in Philadelphia

CPLN 6720 / MUSA 5500 final project. Zhuosi Yang and Veronica Zheng.

Website: https://vrnczay.github.io/philly-ev-charging-access

## Question
Do residents of lower-income areas with limited off-street parking face longer walks to the nearest public Level 2 charger? We also measure driving time to DC fast chargers and compare recorded opening dates of operating stations by tract income.

## Data
| Source | Access | Use |
|---|---|---|
| Alternative Fuel Stations API (NLR) | API | Public, operating stations: location, L2 and DCFC ports, opening date |
| ACS 2023 5-year | Census API | Tract median income; block group attached housing share, zero-vehicle share |
| OPA property assessments | Carto SQL API | Garage spaces per residential parcel, aggregated to garage share |
| TIGER/Line block groups | pygris | 1,338 block group boundaries |
| OpenStreetMap | OSMnx | Walking and driving networks (city + 3.5 km buffer) |

## Repository
```
proposal/                 project proposal (docx) and earlier draft
run_pipeline.bat          runs scripts 01-03 in the `geospatial` conda env
scripts/                  01 collect data, 02 build networks, 03 access metrics
src/                      config.py (paths, parameters), utils.py (shared helpers)
analysis/                 notebooks 01-05, rendered as website pages
_quarto.yml, index.qmd    Quarto website config and home page (builds to docs/)
data/raw/                 downloaded inputs: OPA records, OSM graphs (git-ignored)
data/processed/           pipeline outputs used by the notebooks
data/cache/               OSMnx download cache (git-ignored)
outputs/logs/             pipeline_log.txt
outputs/figures/          exported figures for the report and slides
archive/                  2026-11-17 data feasibility check, reference only
```

## Reproduce
1. Put a Census API key in `census_key.txt` (git-ignored).
2. Run `run_pipeline.bat` (or the three scripts in order) in the course `geospatial` environment.
3. Run the notebooks in `analysis/`, then `quarto render`. The site builds to `docs/` for GitHub Pages.
