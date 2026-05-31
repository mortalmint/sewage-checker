"""
ingest/inspect_dee.py - Phase 2 diagnostic
pyogrio.raw.read returns a 4-tuple: (meta_dict, None, geometries, field_data_list)
"""

import sys
from pathlib import Path

try:
    import pyogrio
except ImportError:
    print("pyogrio not installed.")
    sys.exit(1)

DATA_DIR = Path(__file__).parent.parent / "data"
GPKG_PATH = DATA_DIR / "os_open_rivers.gpkg"


def read_layer(layer, max_features=None):
    """Read a layer, returning (meta, geoms, field_names, field_arrays)."""
    kwargs = dict(layer=layer)
    if max_features:
        kwargs["max_features"] = max_features
    r = pyogrio.raw.read(str(GPKG_PATH), **kwargs)
    meta       = r[0]
    geoms      = r[2]
    field_data = r[3]  # list of arrays, one per field
    field_names = list(meta["fields"]) if meta and "fields" in meta else []
    return meta, geoms, field_names, field_data


def inspect_dee():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        return

    print("Reading watercourse_link (full dataset)...")
    meta, geoms, field_names, field_data = read_layer("watercourse_link")

    n = len(geoms) if geoms is not None else 0
    print(f"Total segments: {n}")
    print(f"Fields: {field_names}")

    if not field_names or not field_data:
        print("No attribute data.")
        return

    fd = {fname: farray for fname, farray in zip(field_names, field_data)}

    # First 10 records
    print(f"\nFirst 10 records:")
    for i in range(min(10, n)):
        print(f"  {i+1}:  id={fd['id'][i]}  "
              f"flow={fd.get('flow_direction', ['?']*n)[i]}  "
              f"start={fd.get('start_node', ['?']*n)[i]}  "
              f"end={fd.get('end_node', ['?']*n)[i]}  "
              f"len={round(fd.get('length', [0]*n)[i], 1)}  "
              f"name={fd.get('watercourse_name', ['?']*n)[i]}")

    # flow_direction summary
    if 'flow_direction' in fd:
        vals = fd['flow_direction']
        unique = {}
        for v in vals:
            k = str(v)
            unique[k] = unique.get(k, 0) + 1
        print(f"\nflow_direction value counts ({n} total segments):")
        for v, count in sorted(unique.items(), key=lambda x: -x[1]):
            print(f"  {v!r:25s} {count:6d}  ({100*count/n:.1f}%)")

    # fictitious summary
    if 'fictitious' in fd:
        vals = fd['fictitious']
        unique = {}
        for v in vals:
            k = str(v)
            unique[k] = unique.get(k, 0) + 1
        print(f"\nfictitious value counts:")
        for v, count in sorted(unique.items(), key=lambda x: -x[1]):
            print(f"  {v!r:25s} {count:6d}  ({100*count/n:.1f}%)")


if __name__ == "__main__":
    inspect_dee()
