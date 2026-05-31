"""
ingest/fetch_river_network.py
 
Downloads river network data for a given catchment.
 
Primary source: Environment Agency Detailed River Network (DRN)
  - Available via the EA's data portal (download, not API)
  - URL: https://www.data.gov.uk/dataset/detailed-river-network
 
Fallback: OS Open Rivers
  - URL: https://www.ordnancesurvey.co.uk/products/os-open-rivers
 
Phase 1.5 smoke test: download the Dee catchment and inspect the schema.
Phase 3 diagnostic: load 2-3 catchments and test connectivity + flow direction.
Phase 4 will build this out fully for national coverage.
 
NOTE: The EA DRN is a bulk download (GeoPackage or Shapefile), not an API.
      This module handles caching the download locally and reading it.
"""
 
import os
from pathlib import Path
 
DATA_DIR = Path(__file__).parent.parent / "data"
 
# EA DRN download — verify current URL at data.gov.uk before Phase 1.5
# The DRN is split by WFD catchment; the Dee is catchment code GB109000
EA_DRN_BASE_URL = "https://environment.data.gov.uk/catchment-planning/WaterBody/{catchment_id}/download"
 
# OS Open Rivers — single national download (~60 MB GeoPackage)
OS_OPEN_RIVERS_URL = "https://api.os.uk/downloads/v1/products/OpenRivers/downloads?area=GB&format=GeoPackage&redirect"
 
 
def get_data_dir() -> Path:
    """Return the local data directory, creating it if needed."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
 
 
def smoke_test_dee() -> None:
    """
    Phase 1.5 smoke test.
    Prints instructions for manually downloading the Dee catchment data
    and checks whether a local copy already exists.
 
    Run from repo root:
        python -c "from ingest.fetch_river_network import smoke_test_dee; smoke_test_dee()"
    """
    dee_path = DATA_DIR / "dee_river_network.gpkg"
 
    print("\n--- River network smoke test: Dee catchment ---")
    print(f"Expected local path: {dee_path}")
 
    if dee_path.exists():
        print(f"File found ({dee_path.stat().st_size / 1e6:.1f} MB). Ready for Phase 3 diagnostic.")
    else:
        print("File not found. To download:")
        print("  1. Go to: https://www.data.gov.uk/dataset/detailed-river-network")
        print("  2. Download the GeoPackage for the Dee / North West catchment area.")
        print("  3. Save to: data/dee_river_network.gpkg")
        print("")
        print("  Alternatively, for a quick check, OS Open Rivers covers the whole")
        print("  of GB in one file (~60 MB):")
        print("  https://www.ordnancesurvey.co.uk/products/os-open-rivers")
        print("  Save as: data/os_open_rivers.gpkg")
 
 
if __name__ == "__main__":
    smoke_test_dee()
