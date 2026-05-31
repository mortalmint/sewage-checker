UK Sewage Upstream Checker
A mobile-friendly web app that tells you which storm overflows are upstream of any point on a river in England (and Wales where data exists), and whether they are currently spilling.
Important caveat: spilling does not mean unsafe. This app reports what is known; it never asserts a safety verdict.
Status
Under construction. See project plan for phase breakdown.
Data sources

Storm overflow spill data — Stream / Water UK National Storm Overflow Hub (ArcGIS feature services, open, no key required)
River network — Environment Agency Detailed River Network (DRN), or OS Open Rivers as fallback
Wales river network — Natural Resources Wales

Tech stack

Python 3.11+
DuckDB (with spatial extension)
NetworkX (directed graph + upstream traversal)
Shapely (geometry / snapping)
Streamlit (UI)
GitHub Actions (scheduled data refresh)
Streamlit Community Cloud (hosting)

Local setup
bashpip install -r requirements.txt
streamlit run app.py
Project structure
app.py                          # Streamlit UI entry point
ingest/
  fetch_spills.py               # Pull spill data from Stream API
  fetch_river_network.py        # Download / cache river network data
graph/
  build_graph.py                # Build directed NetworkX graph from river data
  upstream_query.py             # Upstream traversal and overflow lookup
data/                           # Local data cache (gitignored)
tests/
  test_upstream_query.py        # Unit tests for the traversal algorithm
.github/workflows/
  refresh.yml                   # Scheduled spill data refresh
Caveats and known limitations

Scotland not covered (different data regime under SEPA)
Wales spill data may have patchier coverage than England
Spill data lags reality by up to ~1 hour
The Stream API is operated by Water UK; reliability outside our control
Email alerts provider TBD
