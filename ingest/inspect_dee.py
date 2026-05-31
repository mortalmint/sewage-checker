"""
ingest/inspect_dee.py
 
Phase 2 diagnostic — inspect actual flow_direction values from the Dee.
 
Run from repo root:
    python -m ingest.inspect_dee
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
 
# Dee catchment — wider bbox in EPSG:27700
# Bala to Chester estuary, with margin
# BNG approx: E 280000-380000, N 320000-380000
# Let's go wider to make sure we catch it
DEE_BBOX = (270000, 310000, 385000, 390000)
 
 
def inspect_dee():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        return
 
    print(f"Querying watercourse_link in Dee bbox: {DEE_BBOX}")
 
    result = pyogrio.raw.read(
        str(GPKG_PATH),
        layer="watercourse_link",
        bbox=DEE_BBOX,
    )
 
    geoms       = result[0]
    field_names = list(result[1]) if result[1] is not None else []
    field_data  = list(result[2]) if result[2] is not None else []
 
    n = len(geoms) if geoms is not None else 0
    print(f"Segments found: {n}")
 
    if n == 0:
        print("No segments — try a wider bbox.")
        return
 
    if not field_names:
        print("No attribute fields returned.")
        return
 
    # Print first 10 records
    print(f"\nFirst 10 records:")
    print(f"  {'id':30s} {'flow_direction':20s} {'start_node':30s} {'end_node':30s} {'length':10s} {'name':30s}")
    print(f"  {'-'*30} {'-'*20} {'-'*30} {'-'*30} {'-'*10} {'-'*30}")
 
    fd = {fname: farray for fname, farray in zip(field_names, field_data)}
 
    for i in range(min(10, n)):
        print(f"  {str(fd.get('id', [''])[i]):30s} "
              f"{str(fd.get('flow_direction', [''])[i]):20s} "
              f"{str(fd.get('start_node', [''])[i]):30s} "
              f"{str(fd.get('end_node', [''])[i]):30s} "
              f"{str(round(fd.get('length', [0])[i], 1)):10s} "
              f"{str(fd.get('watercourse_name', [''])[i]):30s}")
 
    # Summarise flow_direction values
    if 'flow_direction' in fd:
        flow_vals = fd['flow_direction']
        unique_vals = set(str(v) for v in flow_vals)
        print(f"\nUnique flow_direction values in this bbox ({n} segments):")
        for v in sorted(unique_vals):
            count = sum(1 for x in flow_vals if str(x) == v)
            print(f"  {v!r:20s} — {count} segments ({100*count/n:.0f}%)")
 
    # Check for None/null flow_direction
    if 'flow_direction' in fd:
        nulls = sum(1 for v in fd['flow_direction'] if v is None or str(v) in ('None', ''))
        print(f"\nNull/missing flow_direction: {nulls}/{n} ({100*nulls/n:.0f}%)")
 
 
if __name__ == "__main__":
    inspect_dee()
