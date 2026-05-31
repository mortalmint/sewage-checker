"""
ingest/inspect_dee.py

Phase 2 diagnostic — inspect actual flow_direction values.
Reads full dataset and filters manually to avoid bbox issues.

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


def inspect_dee():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        return

    print("Reading full watercourse_link layer (may take a few seconds)...")

    result = pyogrio.raw.read(
        str(GPKG_PATH),
        layer="watercourse_link",
    )

    geoms       = result[0]
    field_names = list(result[1]) if result[1] is not None else []
    field_data  = result[2] if result[2] is not None else []

    n = len(geoms) if geoms is not None else 0
    print(f"Total segments loaded: {n}")
    print(f"Fields: {field_names}")

    if not field_names or field_data is None:
        print("No attribute data returned — unexpected.")
        return

    fd = {fname: farray for fname, farray in zip(field_names, field_data)}

    # Print first 10 records regardless of location
    print(f"\nFirst 10 records (any location):")
    for i in range(min(10, n)):
        row = {k: fd[k][i] for k in field_names}
        print(f"  {i+1}: {row}")

    # Summarise flow_direction across all segments
    if 'flow_direction' in fd:
        flow_vals = fd['flow_direction']
        unique_vals = set(str(v) for v in flow_vals)
        print(f"\nflow_direction unique values (all {n} segments):")
        for v in sorted(unique_vals):
            count = sum(1 for x in flow_vals if str(x) == v)
            print(f"  {v!r:20s} — {count} ({100*count/n:.0f}%)")

        nulls = sum(1 for v in flow_vals if v is None or str(v) in ('None', ''))
        print(f"\nNull/empty: {nulls}/{n} ({100*nulls/n:.0f}%)")
    else:
        print("\nNo flow_direction field found.")

    # Summarise fictitious field
    if 'fictitious' in fd:
        fict_vals = fd['fictitious']
        unique_fict = set(str(v) for v in fict_vals)
        print(f"\nfictitious unique values:")
        for v in sorted(unique_fict):
            count = sum(1 for x in fict_vals if str(x) == v)
            print(f"  {v!r:20s} — {count} ({100*count/n:.0f}%)")


if __name__ == "__main__":
    inspect_dee()
