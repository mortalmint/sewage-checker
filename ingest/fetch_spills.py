"""
ingest/fetch_spills.py
 
Fetches near-real-time storm overflow spill data from the Stream / Water UK
National Storm Overflow Hub.
 
Data is a single unified ArcGIS Online feature service covering all companies
in England and Wales. No API key or registration required; publicly open.
 
Phase 5 will build this out fully. This file is a stub with working
smoke-test functions for Phase 1.4.
"""
 
import requests
import json
 
# ---------------------------------------------------------------------------
# Single unified Stream service — all ~14,000 overflows in one layer.
# Confirmed URL from ArcGIS item 333c5c0600f94757b134b276ac4ad8b0.
# Layer 0 = outfall locations with current spill status.
# ---------------------------------------------------------------------------
 
STREAM_SERVICE_BASE = (
    "https://services3.arcgis.com/VCOY1atHWVcDlvlJ/arcgis/rest/services"
    "/stream_service_outfall_locations_view/FeatureServer/0"
)
 
# To filter by company, use a WHERE clause on whatever company field exists.
# The smoke test will reveal the actual field names — we don't know them yet.
 
 
def query_layer(base_url: str, where: str = "1=1", out_fields: str = "*",
                result_record_count: int = 5) -> dict:
    """
    Query an ArcGIS FeatureServer layer and return the raw JSON response.
 
    Args:
        base_url: FeatureServer layer URL (without /query)
        where: SQL WHERE clause
        out_fields: comma-separated field names, or "*" for all
        result_record_count: max records to return (set low for smoke tests)
 
    Returns:
        Parsed JSON dict from the ArcGIS REST API
    """
    url = f"{base_url}/query"
    params = {
        "where": where,
        "outFields": out_fields,
        "returnGeometry": "true",
        "outSR": "4326",          # WGS84 lat/lon
        "f": "json",
        "resultRecordCount": result_record_count,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
 
 
def smoke_test() -> None:
    """
    Phase 1.4 smoke test. Queries 2 records from the unified Stream service
    and prints the result so we can confirm the shape of the data.
 
    Run from the repo root:
        python -c "from ingest.fetch_spills import smoke_test; smoke_test()"
    """
    print("\n--- Smoke test: Stream unified service ---")
    base_url = STREAM_SERVICE_BASE
    print(f"URL: {base_url}")
 
    try:
        data = query_layer(base_url, result_record_count=2)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        return
 
    if "error" in data:
        print(f"ArcGIS error: {data['error']}")
        return
 
    features = data.get("features", [])
    print(f"Records returned: {len(features)}")
    if features:
        print("First record attributes:")
        print(json.dumps(features[0].get("attributes", {}), indent=2))
        print("First record geometry (lon, lat):")
        geom = features[0].get("geometry", {})
        print(f"  x={geom.get('x')}, y={geom.get('y')}")
    else:
        print("No features returned.")
 
 
if __name__ == "__main__":
    smoke_test()
