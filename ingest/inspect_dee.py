"""
ingest/inspect_dee.py - Phase 2 diagnostic
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


def inspect_dee():
    if not GPKG_PATH.exists():
        print(f"File not found: {GPKG_PATH}")
        return

    # Try reading by layer index instead of name
    print("Trying layer index 0 (hydro_node)...")
    r = pyogrio.raw.read(str(GPKG_PATH), layer=0, max_features=3)
    print(f"  result type: {type(r)}, length: {len(r)}")
    for i, item in enumerate(r):
        print(f"  result[{i}]: type={type(item)}, value={repr(item)[:200]}")

    print("\nTrying layer index 1 (watercourse_link)...")
    r = pyogrio.raw.read(str(GPKG_PATH), layer=1, max_features=3)
    print(f"  result type: {type(r)}, length: {len(r)}")
    for i, item in enumerate(r):
        print(f"  result[{i}]: type={type(item)}, value={repr(item)[:200]}")

    print("\nTrying layer by name 'watercourse_link'...")
    r = pyogrio.raw.read(str(GPKG_PATH), layer="watercourse_link", max_features=3)
    print(f"  result type: {type(r)}, length: {len(r)}")
    for i, item in enumerate(r):
        print(f"  result[{i}]: type={type(item)}, value={repr(item)[:200]}")


if __name__ == "__main__":
    inspect_dee()
