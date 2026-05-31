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
DEE_BBOX_BNG = (280000, 330000, 340000, 380000)


def read_sample(gpkg_path, layer_name, bbox=None, max_features=3):
    """Read a small sample, returning (field_names, rows) safely."""
    kwargs = dict(layer=layer_name, max_features=max_features)
    if bbox:
        kwargs["bbox"] = bbox
    result = pyogrio.raw.read(str(gpkg_path), **kwargs)
    # result is (geometry, field_names, field_data, ...)
    # field_names may be a list; field_data may be None or a list of arrays
    field_names = result[1] if result[1] is not None else []
    field_data  = result[2] if result[2] is not None else []
    if len(field_names) == 0 or len(field_data) == 0:
        return [], []
    n = len(field_data[0])
    rows = []
    for i in range(min(max_features, n)):
        rows.append({fname: farray[i] for fname, farray in zip(field_names, field_data)})
    return field_names, rows


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

        flow_candidates = [
            f for f in info['fields']
            if any(kw in f.lower() for kw in
                   ["flow", "direct", "from", "to", "start", "end",
                    "up", "down", "source", "mouth", "node", "link"])
        ]
        if flow_candidates:
            print(f"\n  *** Possible flow/topology fields: {flow_candidates} ***")

        field_names, rows = read_sample(GPKG_PATH, layer_name)
        if rows:
            print(f"\nSample records (first {len(rows)}):")
            for i, row in enumerate(rows):
                print(f"  Record {i+1}:")
                for fname, val in row.items():
                    print(f"    {fname:35s} {repr(val)}")
        else:
            print("\n  (no attribute data returned for this layer)")

    # Dee bbox clip
    print(f"\n{'='*60}")
    print(f"Dee catchment clip (watercourse_link)")
    print('='*60)
    print(f"Bbox (BNG): {DEE_BBOX_BNG}")

    info_wl = pyogrio.read_info(str(GPKG_PATH), layer="watercourse_link")
    result = pyogrio.raw.read(str(GPKG_PATH), layer="watercourse_link", bbox=DEE_BBOX_BNG)
    geoms       = result[0]
    field_names = result[1] if result[1] is not None else []
    field_data  = result[2] if result[2] is not None else []

    n = len(geoms) if geoms is not None else 0
    print(f"Total segments (GB): {info_wl['features']}")
    print(f"Segments in Dee bbox: {n}")

    if n > 0 and field_names and field_data:
        print(f"\nFirst Dee segment:")
        for fname, farray in zip(field_names, field_data):
            print(f"  {fname:35s} {repr(farray[0])}")


if __name__ == "__main__":
    inspect()
