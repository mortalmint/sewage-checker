"""
ingest/inspect_river_network.py
 
Phase 1.5 / Phase 3 diagnostic tool.
Inspects the OS Open Rivers GeoPackage and reports:
  - What layers are in the file
  - What fields each layer has
  - Whether any field looks like flow direction
  - A sample of records from the Dee catchment area
 
Run from repo root:
    python -m ingest.inspect_river_network
"""
 
import sys
from pathlib import Path
 
try:
    import geopandas as gpd
except ImportError:
    print("geopandas not installed. Run: pip install geopandas")
    sys.exit(1)
 
DATA_DIR = Path(__file__).parent.parent / "data"
GPKG_PATH = DATA_DIR / "os_open_rivers.gpkg"
 
# Rough bounding box for the Dee catchment (lon/lat, WGS84)
# Covers the river from Bala Lake down to the estuary at Chester
DEE_BBOX = (-3.6, 52.8, -2.8, 53.3)  # (minx, miny, maxx, maxy)
 
 
def inspect():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        print("Save OS Open Rivers GeoPackage to: data/os_open_rivers.gpkg")
        return
 
    print(f"\nFile: {GPKG_PATH} ({GPKG_PATH.stat().st_size / 1e6:.1f} MB)")
 
    # List layers
    import fiona
    layers = fiona.listlayers(str(GPKG_PATH))
    print(f"\nLayers in file ({len(layers)}):")
    for layer in layers:
        print(f"  - {layer}")
 
    # Inspect each layer
    for layer in layers:
        print(f"\n{'='*60}")
        print(f"Layer: {layer}")
        print('='*60)
 
        gdf = gpd.read_file(GPKG_PATH, layer=layer, rows=5)
        print(f"CRS: {gdf.crs}")
        print(f"Geometry type: {gdf.geom_type.unique().tolist()}")
        print(f"Fields ({len(gdf.columns)}):")
        for col in gdf.columns:
            dtype = gdf[col].dtype
            sample = gdf[col].dropna().iloc[0] if not gdf[col].dropna().empty else "N/A"
            print(f"  {col:35s} {str(dtype):12s}  e.g. {sample!r}")
 
        # Flag anything that looks like flow direction
        flow_candidates = [
            c for c in gdf.columns
            if any(kw in c.lower() for kw in ["flow", "direction", "from", "to", "start", "end", "up", "down"])
        ]
        if flow_candidates:
            print(f"\n  *** Possible flow-direction fields: {flow_candidates} ***")
        else:
            print("\n  (No obvious flow-direction fields found in this layer)")
 
    # Now load just the Dee area from the first line/polyline layer
    line_layers = []
    for layer in layers:
        gdf_sample = gpd.read_file(GPKG_PATH, layer=layer, rows=1)
        if gdf_sample.geom_type.iloc[0] in ("LineString", "MultiLineString"):
            line_layers.append(layer)
 
    if line_layers:
        print(f"\n{'='*60}")
        print(f"Dee catchment sample (layer: {line_layers[0]})")
        print('='*60)
        gdf_full = gpd.read_file(GPKG_PATH, layer=line_layers[0])
 
        # Reproject to WGS84 if needed
        if gdf_full.crs and gdf_full.crs.to_epsg() != 4326:
            gdf_full = gdf_full.to_crs(epsg=4326)
 
        minx, miny, maxx, maxy = DEE_BBOX
        dee = gdf_full.cx[minx:maxx, miny:maxy]
        print(f"Total segments in GB: {len(gdf_full)}")
        print(f"Segments in Dee bounding box: {len(dee)}")
        if len(dee) > 0:
            print("\nSample Dee record:")
            print(dee.iloc[0].drop("geometry").to_string())
        else:
            print("No segments found in Dee bounding box — check the CRS or bbox.")
 
 
if __name__ == "__main__":
    inspect()
