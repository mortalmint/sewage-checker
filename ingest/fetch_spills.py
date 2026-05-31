"""
ingest/fetch_spills.py
 
Fetches near-real-time storm overflow spill data from the Stream / Water UK
National Storm Overflow Hub.
 
Data is hosted as ArcGIS Online feature services — one per water company.
No API key or registration required; these are publicly open.
 
Phase 5 will build this out fully. This file is a stub with working
smoke-test functions for Phase 1.4.
"""
 
import requests
import json
 
# ---------------------------------------------------------------------------
# ArcGIS feature service endpoints — one per water company.
# Each URL points to a hosted FeatureServer layer on ArcGIS Online.
# Format: .../FeatureServer/0/query
# ---------------------------------------------------------------------------
 
COMPANY_ENDPOINTS = {
    "anglian":      "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Anglian_Water_Storm_Overflow_Activity/FeatureServer/0",
    "southern":     "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Southern_Water_Storm_Overflow_Activity/FeatureServer/0",
    "united_util":  "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/United_Utilities_Storm_Overflow_Activity/FeatureServer/0",
    "severn_trent": "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Severn_Trent_Storm_Overflow_Activity/FeatureServer/0",
    "thames":       "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Thames_Water_Storm_Overflow_Activity/FeatureServer/0",
    "yorkshire":    "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Yorkshire_Water_Storm_Overflow_Activity/FeatureServer/0",
    "wessex":       "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Wessex_Water_Storm_Overflow_Activity/FeatureServer/0",
    "northumbrian": "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Northumbrian_Water_Storm_Overflow_Activity/FeatureServer/0",
    "southwest":    "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/South_West_Water_Storm_Overflow_Activity/FeatureServer/0",
    # Welsh Water included in England hub where data exists
    "welsh":        "https://services-eu1.arcgis.com/KTiEIlGFdtIE0S0h/arcgis/rest/services/Welsh_Water_Storm_Overflow_Activity/FeatureServer/0",
}
 
# NOTE: The exact service names above are educated guesses based on the
# naming convention visible in the Stream portal item IDs. They MUST be
# verified in Phase 1.4 (smoke test). If any 404, check:
# https://portal-streamwaterdata.hub.arcgis.com/
# and find the actual FeatureServer URL for each company's dataset.
 
 
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
 
 
def smoke_test(company: str = "anglian") -> None:
    """
    Phase 1.4 smoke test. Queries 2 records from one company's feed
    and prints the result so we can confirm the shape of the data.
 
    Run from the repo root:
        python -c "from ingest.fetch_spills import smoke_test; smoke_test()"
    """
    print(f"\n--- Smoke test: {company} ---")
    base_url = COMPANY_ENDPOINTS[company]
    print(f"URL: {base_url}")
 
    try:
        data = query_layer(base_url, result_record_count=2)
    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        print("The service URL may need updating — check the Stream portal.")
        return
 
    if "error" in data:
        print(f"ArcGIS error: {data['error']}")
        print("The service URL may need updating — check the Stream portal.")
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
        print("No features returned — check the WHERE clause or endpoint.")
 
 
if __name__ == "__main__":
    smoke_test()
