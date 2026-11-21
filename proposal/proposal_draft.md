# Final Project Proposal

**Plugged In or Left Out? The Rollout and Reach of Public EV Charging in Philadelphia**

Team: Muyan (Veronica) Zheng, [Partner Name]
Course: CPLN 6720 / MUSA 5500, Geospatial Data Science in Python

## Research Questions
1. How has Philadelphia's public EV charging network expanded since 2019, and which neighborhoods received chargers first?
2. Which block groups are furthest from public charging by walking distance, and do these gaps overlap with lower income and rowhouse-dominated blocks where residents cannot charge at home?
3. What neighborhood characteristics best predict whether a block group gained access to public charging early?

## Motivation
More than half of Philadelphia's housing units are single-family attached homes (56% in ACS 2023), and most have no driveway or garage. Residents of these blocks depend on public chargers to switch to electric vehicles. If chargers follow income rather than need, public charging could widen existing transportation inequities. This project measures where the network has grown, who it reaches, and where new chargers would close the largest gaps.

## Data
| Source | Access | Use |
|---|---|---|
| NLR (formerly NREL) Alternative Fuel Stations API | API | Public, available EV stations with location, network, Level 2 and DC fast port counts, and open date (183 stations in Philadelphia) |
| Census ACS 5-year 2023 | Census API | Median household income (tract); housing type and household vehicle availability (block group) |
| Census TIGER block groups | pygris | 1,338 block group boundaries |
| OpenStreetMap | OSMnx | Citywide walking network (about 149,000 nodes and 464,000 edges) |
| City of Philadelphia building footprints | ArcGIS REST API | Building density as a control variable (546,089 buildings) |

All five sources were downloaded and tested in our environment before submitting this proposal.

## Methods
1. **Data collection:** Query the station and Census APIs, download block group boundaries and the walking network, and join everything to block groups.
2. **Rollout timeline (2019 to 2026):** Use station open dates to map the network year by year and compare growth across charging networks and neighborhood income groups.
3. **Access gaps:** Compute the shortest walking distance from each block group centroid to the nearest charger with OSMnx and multi-source Dijkstra, then overlay income, rowhouse share, and zero-vehicle households.
4. **Who got chargers first:** Train a random forest classifier (scikit-learn) to predict whether a block group had a charger within walking range by 2022, and use feature importance to identify the drivers. Then apply K-means clustering to group block groups into charging gap types and identify priority areas for new public chargers.

## Preliminary Result
A first run shows a median walking distance of 1.6 km from a block group to the nearest public charger. About half of all block groups (659 of 1,338) are more than one mile away, so access varies widely across the city.

## Course Requirements Met
- Data collected through APIs (station API, Census API)
- Data combined from three or more sources
- Reasonably complex geospatial analysis (spatial joins, network distance, temporal aggregation)
- Street network analysis with OSMnx
- Clustering analysis with scikit-learn
- Machine learning analysis with scikit-learn

## Deliverables
- A multi-page Quarto website published on GitHub Pages, with pages for data collection, rollout timeline, access gaps, and drivers and priority areas, including interactive maps
- A GitHub repository with all code and a README linking to the website
- A 10-minute presentation on December 4 and a report of about 3 pages on December 8

## Limitations
- The station database lists only currently operating stations, so the timeline shows the opening order of existing stations, not stations that have closed.
- Neighborhood-level EV ownership data is not publicly available, so demand is approximated with housing type, vehicle availability, and income.
- Pricing data is incomplete (about 10% of stations), so the project focuses on access rather than cost.

## Division of Work
- [Veronica]: network analysis, modeling, clustering
- [Partner]: data collection and cleaning, timeline maps, website
- Shared: research design, report, presentation
