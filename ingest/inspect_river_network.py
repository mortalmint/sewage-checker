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
    import pyogrio
except ImportError:
    print("pyogrio not installed. Run: pip install pyogrio")
    sys.exit(1)
 
DATA_DIR = Path(__file__).parent.parent / "data"
GPKG_PATH = DATA_DIR / "oprvrs_gb.gpkg"
 
# Rough bounding box for the Dee catchment (lon/lat, WGS84)
# Covers the river from Bala Lake down to the estuary at Chester
DEE_BBOX = (-3.6, 52.8, -2.8, 53.3)  # (minx, miny, maxx, maxy)
 
 
def inspect():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        print("Save OS Open Rivers GeoPackage to: data/oprvrs_gb.gpkg")
        return
 
    print(f"\nFile: {GPKG_PATH} ({GPKG_PATH.stat().st_size / 1e6:.1f} MB)")
 
    # List layers
    layers = pyogrio.list_layers(str(GPKG_PATH))
    print(f"\nLayers in file ({len(layers)}):")
    for layer in layers:
        print(f"  - {layer[0]}  (geometry: {layer[1]})")
 
    # Inspect each layer
    for layer_info in layers:
        layer_name = layer_info[0]
        print(f"\n{'='*60}")
        print(f"Layer: {layer_name}")
        print('='*60)
 
        info = pyogrio.read_info(str(GPKG_PATH), layer=layer_name)
        print(f"CRS: {info['crs']}")
        print(f"Feature count: {info['features']}")
        print(f"Geometry type: {info['geometry_type']}")
        print(f"Bounds: {info['total_bounds']}")
 
        # Read a small sample to see field values
        data = pyogrio.read_dataframe(str(GPKG_PATH), layer=layer_name, max_features=5)
        print(f"\nFields ({len(data.columns)}):")
        for col in data.columns:
            if col == "geometry":
                continue
            dtype = data[col].dtype
            sample = data[col].dropna().iloc[0] if not data[col].dropna().empty else "N/A"
            print(f"  {col:35s} {str(dtype):12s}  e.g. {repr(sample)}")
 
        # Flag anything that looks like flow direction
        flow_candidates = [
            c for c in data.columns
            if any(kw in c.lower() for kw in
                   ["flow", "direction", "from", "to", "start", "end", "up", "down", "source", "mouth"])
        ]
        if flow_candidates:
            print(f"\n  *** Possible flow-direction fields: {flow_candidates} ***")
        else:
            print("\n  (No obvious flow-direction fields found in this layer)")
 
    # Dee catchment sample — find the line layer and clip to bbox
    line_layers = [l[0] for l in layers if "line" in l[0].lower() or "watercourse" in l[0].lower() or l[1] in ("LineString", "MultiLineString", "Unknown")]
    if not line_layers:
        line_layers = [layers[0][0]]  # fall back to first layer
 
    print(f"\n{'='*60}")
    print(f"Dee catchment sample (layer: {line_layers[0]})")
    print('='*60)
 
    minx, miny, maxx, maxy = DEE_BBOX
    dee_data = pyogrio.read_dataframe(
        str(GPKG_PATH),
        layer=line_layers[0],
        bbox=(minx, miny, maxx, maxy),
    )
    print(f"Segments in Dee bounding box: {len(dee_data)}")
    if len(dee_data) > 0:
        print("\nFirst Dee record (non-geometry fields):")
        row = dee_data.iloc[0].drop("geometry") if "geometry" in dee_data.columns else dee_data.iloc[0]
        for field, val in row.items():
            print(f"  {field:35s} {repr(val)}")
    else:
        print("No segments found in Dee bounding box.")
        print("The file may use a different CRS — check the bounds printed above.")
 
 
if __name__ == "__main__":
    inspect()
