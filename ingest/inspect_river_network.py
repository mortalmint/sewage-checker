"""
ingest/inspect_river_network.py
 
Phase 1.5 / Phase 3 diagnostic tool.
Uses pyogrio's raw read() — no geopandas required.
 
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
GPKG_PATH = DATA_DIR / "os_open_rivers.gpkg"
 
# Dee catchment bounding box in EPSG:27700 (British National Grid, metres)
# Converted from lon/lat (-3.6, 52.8, -2.8, 53.3)
DEE_BBOX_BNG = (280000, 330000, 340000, 380000)  # (minx, miny, maxx, maxy)
 
 
def inspect():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        return
 
    print(f"\nFile: {GPKG_PATH} ({GPKG_PATH.stat().st_size / 1e6:.1f} MB)")
 
    layers = pyogrio.list_layers(str(GPKG_PATH))
    print(f"\nLayers ({len(layers)}):")
    for layer in layers:
        print(f"  - {layer[0]}  (geometry: {layer[1]})")
 
    for layer_info in layers:
        layer_name = layer_info[0]
        print(f"\n{'='*60}")
        print(f"Layer: {layer_name}")
        print('='*60)
 
        info = pyogrio.read_info(str(GPKG_PATH), layer=layer_name)
        print(f"CRS:            {info['crs']}")
        print(f"Feature count:  {info['features']}")
        print(f"Geometry type:  {info['geometry_type']}")
        print(f"Bounds:         {info['total_bounds']}")
        print(f"\nFields:")
        for field_name, field_type in zip(info['fields'], info['dtypes']):
            print(f"  {field_name:35s} {field_type}")
 
        # Flag flow-direction candidates
        flow_candidates = [
            f for f in info['fields']
            if any(kw in f.lower() for kw in
                   ["flow", "direct", "from", "to", "start", "end",
                    "up", "down", "source", "mouth", "node", "link"])
        ]
        if flow_candidates:
            print(f"\n  *** Possible flow/topology fields: {flow_candidates} ***")
 
        # Read 3 sample records using raw API
        result = pyogrio.raw.read(
            str(GPKG_PATH),
            layer=layer_name,
            max_features=3,
        )
        field_names = result[1]
        field_data  = result[2]
        print(f"\nSample records (first 3):")
        for i in range(min(3, len(field_data[0]) if field_data else 0)):
            print(f"  Record {i+1}:")
            for fname, farray in zip(field_names, field_data):
                print(f"    {fname:35s} {repr(farray[i])}")
 
    # Dee bbox clip on watercourse_link
    print(f"\n{'='*60}")
    print(f"Dee catchment clip (watercourse_link)")
    print('='*60)
    print(f"Bbox (BNG): {DEE_BBOX_BNG}")
 
    result = pyogrio.raw.read(
        str(GPKG_PATH),
        layer="watercourse_link",
        bbox=DEE_BBOX_BNG,
    )
    field_names = result[1]
    field_data  = result[2]
    n_features  = len(field_data[0]) if field_data else 0
    print(f"Segments in Dee bbox: {n_features}")
 
    if n_features > 0:
        print(f"\nFirst Dee segment:")
        for fname, farray in zip(field_names, field_data):
            print(f"  {fname:35s} {repr(farray[0])}")
 
 
if __name__ == "__main__":
    inspect()
