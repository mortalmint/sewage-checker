"""
graph/upstream_query.py
 
Core upstream traversal algorithm.
 
Given:
  - A directed river graph (edges point downstream: from -> to)
  - A query point (lat, lon) on or near a river
  - A set of overflow points with spill status
 
Returns:
  - All overflows that are hydrologically upstream of the query point
  - For each: distance along river (m), spill status, time since last event
 
This module is self-contained and testable without any real data.
Run it directly to see the algorithm working on a synthetic river network:
 
    python -m graph.upstream_query
 
The synthetic network looks like this (flow direction = downstream = rightward):
 
    A ---5km--- B ---3km--- C ---4km--- D  (main stem)
                    |
                   2km
                    |
                    E ---6km--- F          (tributary)
 
    Query point: between C and D (at C for simplicity)
    Overflows at: A, B, E, F
    Expected result: A (8km upstream), B (3km upstream), E (2km upstream),
                     F (8km upstream via E).
    NOT returned: D (downstream of query point).
"""
 
import networkx as nx
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
import math
from dataclasses import dataclass, field
from typing import Optional
 
 
# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
 
@dataclass
class Overflow:
    """A storm overflow with location and current spill status."""
    id: str
    name: str
    lat: float
    lon: float
    # Spill status: "spilling", "recent" (spilled in last 24h), "dry", "unknown"
    status: str = "unknown"
    # ISO8601 string or None
    last_event_start: Optional[str] = None
    last_event_end: Optional[str] = None
    # Set during snapping — the graph node this overflow is snapped to
    snapped_node: Optional[str] = None
    snapped_distance_m: float = 0.0
 
 
@dataclass
class UpstreamResult:
    """An overflow found upstream of the query point."""
    overflow: Overflow
    # Distance along the river network from query point to overflow (metres)
    river_distance_m: float
 
    @property
    def river_distance_km(self) -> float:
        return self.river_distance_m / 1000.0
 
    def __repr__(self):
        return (
            f"UpstreamResult(id={self.overflow.id!r}, "
            f"status={self.overflow.status!r}, "
            f"distance={self.river_distance_km:.1f}km)"
        )
 
 
# ---------------------------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------------------------
 
def build_graph_from_segments(segments: list[dict]) -> nx.DiGraph:
    """
    Build a directed graph from a list of river segment dicts.
 
    Each segment dict must have:
      - "from_node": str  (upstream end node ID)
      - "to_node": str    (downstream end node ID)
      - "length_m": float (segment length in metres)
      - "from_coord": (lon, lat) tuple
      - "to_coord": (lon, lat) tuple
 
    Edges point downstream (from_node -> to_node).
    To find upstream nodes, traverse edges in reverse.
    """
    G = nx.DiGraph()
    for seg in segments:
        G.add_edge(
            seg["from_node"],
            seg["to_node"],
            length_m=seg["length_m"],
            from_coord=seg["from_coord"],
            to_coord=seg["to_coord"],
        )
    return G
 
 
def snap_point_to_graph(lat: float, lon: float, G: nx.DiGraph) -> tuple[str, float]:
    """
    Find the nearest node in the graph to a given (lat, lon) point.
 
    Returns:
        (node_id, distance_m) — the nearest node and straight-line distance to it.
 
    In Phase 6 this will be upgraded to snap to the nearest *edge* (not just node)
    and split the edge, for more accurate distance calculations.
    For now, nearest-node is good enough to validate the algorithm.
    """
    query_pt = Point(lon, lat)
    best_node = None
    best_dist = float("inf")
 
    for node in G.nodes():
        coord = G.nodes[node].get("coord")
        if coord is None:
            # Try to infer coord from edges
            for u, v, data in G.edges(node, data=True):
                if u == node:
                    coord = data.get("from_coord")
                    break
            for u, v, data in G.in_edges(node, data=True):
                if v == node:
                    coord = data.get("to_coord")
                    break
        if coord:
            dist = query_pt.distance(Point(coord[0], coord[1]))
            if dist < best_dist:
                best_dist = dist
                best_node = node
 
    # Convert degree distance to approximate metres (rough, good enough for snapping)
    best_dist_m = best_dist * 111_000
    return best_node, best_dist_m
 
 
def find_upstream_nodes(G: nx.DiGraph, start_node: str) -> dict[str, float]:
    """
    Find all nodes upstream of start_node, with accumulated river distance.
 
    Traverses edges in reverse (upstream direction).
    Returns {node_id: distance_m_from_start}.
    """
    upstream = {}
    queue = [(start_node, 0.0)]
 
    while queue:
        current, dist_so_far = queue.pop()
        # In-edges of current node = edges coming FROM upstream nodes
        for upstream_node, _, edge_data in G.in_edges(current, data=True):
            seg_length = edge_data.get("length_m", 0.0)
            new_dist = dist_so_far + seg_length
            if upstream_node not in upstream or upstream[upstream_node] > new_dist:
                upstream[upstream_node] = new_dist
                queue.append((upstream_node, new_dist))
 
    return upstream
 
 
# ---------------------------------------------------------------------------
# Main query function
# ---------------------------------------------------------------------------
 
def query_upstream_overflows(
    lat: float,
    lon: float,
    G: nx.DiGraph,
    overflows: list[Overflow],
    max_distance_m: float = float("inf"),
) -> list[UpstreamResult]:
    """
    Find all overflows upstream of the given point.
 
    Args:
        lat, lon: the query point (user's chosen location on the river)
        G: directed river graph (edges point downstream)
        overflows: list of Overflow objects with snapped_node set
        max_distance_m: optional cap — ignore overflows further than this
 
    Returns:
        List of UpstreamResult, sorted by river distance (nearest first).
    """
    # 1. Snap the query point to the nearest graph node
    query_node, snap_dist = snap_point_to_graph(lat, lon, G)
    if query_node is None:
        return []
 
    # 2. Find all upstream nodes and their distances
    upstream_nodes = find_upstream_nodes(G, query_node)
 
    # 3. Match overflows to upstream nodes
    results = []
    for overflow in overflows:
        if overflow.snapped_node is None:
            continue
        if overflow.snapped_node in upstream_nodes:
            dist = upstream_nodes[overflow.snapped_node]
            if dist <= max_distance_m:
                results.append(UpstreamResult(overflow=overflow, river_distance_m=dist))
 
    # 4. Sort nearest first
    results.sort(key=lambda r: r.river_distance_m)
    return results
 
 
def plain_english_verdict(results: list[UpstreamResult]) -> str:
    """
    Generate the plain-English summary shown at the top of the UI.
 
    Examples:
      "No overflows upstream within 20 km."
      "1 overflow spilling now, 3.2 km upstream."
      "2 overflows spilling now within 10 km upstream. 1 further overflow spilled in the last 24 hours."
    """
    if not results:
        return "No monitored overflows found upstream of this point."
 
    spilling_now = [r for r in results if r.overflow.status == "spilling"]
    recent = [r for r in results if r.overflow.status == "recent"]
    dry = [r for r in results if r.overflow.status == "dry"]
    unknown = [r for r in results if r.overflow.status == "unknown"]
 
    parts = []
 
    if spilling_now:
        n = len(spilling_now)
        nearest_km = spilling_now[0].river_distance_km
        noun = "overflow" if n == 1 else "overflows"
        parts.append(f"⚠️ {n} {noun} spilling now (nearest: {nearest_km:.1f} km upstream)")
 
    if recent:
        n = len(recent)
        noun = "overflow" if n == 1 else "overflows"
        parts.append(f"{n} {noun} spilled in the last 24 hours")
 
    if not spilling_now and not recent:
        n = len(dry) + len(unknown)
        noun = "overflow" if n == 1 else "overflows"
        parts.append(f"✅ {n} upstream {noun}, none currently spilling")
 
    verdict = ". ".join(parts) + "."
    verdict += "\n\n*Spilling does not mean unsafe. This app reports what is known; it does not make a safety judgement.*"
    return verdict
 
 
# ---------------------------------------------------------------------------
# Synthetic test / PoC demo
# ---------------------------------------------------------------------------
 
def _build_synthetic_network() -> tuple[nx.DiGraph, list[Overflow]]:
    """
    Build the synthetic river network described in the module docstring.
 
        A ---5km--- B ---3km--- C ---4km--- D  (main stem, flows A→B→C→D)
                        |
                       2km
                        |
                        E ---6km--- F          (tributary, flows F→E→B)
 
    Nodes: A, B, C, D, E, F
    Overflows at: A, B, E, F (with varying statuses)
    Query point: at node C
    """
    segments = [
        {"from_node": "A", "to_node": "B", "length_m": 5000,
         "from_coord": (0.00, 52.00), "to_coord": (0.05, 52.00)},
        {"from_node": "B", "to_node": "C", "length_m": 3000,
         "from_coord": (0.05, 52.00), "to_coord": (0.08, 52.00)},
        {"from_node": "C", "to_node": "D", "length_m": 4000,
         "from_coord": (0.08, 52.00), "to_coord": (0.12, 52.00)},
        {"from_node": "E", "to_node": "B", "length_m": 2000,
         "from_coord": (0.05, 52.02), "to_coord": (0.05, 52.00)},
        {"from_node": "F", "to_node": "E", "length_m": 6000,
         "from_coord": (0.05, 52.07), "to_coord": (0.05, 52.02)},
    ]
 
    G = build_graph_from_segments(segments)
 
    overflows = [
        Overflow(id="OVF-A", name="Overflow at A", lat=52.00, lon=0.00,
                 status="spilling", snapped_node="A"),
        Overflow(id="OVF-B", name="Overflow at B", lat=52.00, lon=0.05,
                 status="recent", snapped_node="B"),
        Overflow(id="OVF-E", name="Overflow at E", lat=52.02, lon=0.05,
                 status="dry", snapped_node="E"),
        Overflow(id="OVF-F", name="Overflow at F", lat=52.07, lon=0.05,
                 status="spilling", snapped_node="F"),
        Overflow(id="OVF-D", name="Overflow at D (downstream)", lat=52.00, lon=0.12,
                 status="spilling", snapped_node="D"),
    ]
 
    return G, overflows
 
 
def run_poc_demo():
    """Run the algorithm on the synthetic network and print results."""
    print("=" * 60)
    print("Upstream Sewage Checker — Algorithm PoC")
    print("=" * 60)
 
    G, overflows = _build_synthetic_network()
 
    # Query point: at node C (lat=52.00, lon=0.08)
    query_lat, query_lon = 52.00, 0.08
    print(f"\nQuery point: lat={query_lat}, lon={query_lon} (node C)")
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Overflows: {len(overflows)} total")
 
    results = query_upstream_overflows(query_lat, query_lon, G, overflows)
 
    print(f"\nUpstream overflows found: {len(results)}")
    print("-" * 40)
    for r in results:
        print(f"  {r.overflow.id:10s}  status={r.overflow.status:8s}  "
              f"distance={r.river_distance_km:.1f} km")
 
    print("\nExpected:")
    print("  OVF-A   spilling   8.0 km  (5km A→B + 3km B→C)")
    print("  OVF-B   recent     3.0 km  (3km B→C)")
    print("  OVF-E   dry        5.0 km  (2km E→B + 3km B→C)")
    print("  OVF-F   spilling  11.0 km  (6km F→E + 2km E→B + 3km B→C)")
    print("  OVF-D should NOT appear (it is downstream of C)")
 
    print("\n" + "=" * 60)
    print("Plain-English verdict:")
    print("=" * 60)
    print(plain_english_verdict(results))
 
    # Verify correctness
    result_ids = {r.overflow.id for r in results}
    assert "OVF-A" in result_ids, "FAIL: OVF-A should be upstream"
    assert "OVF-B" in result_ids, "FAIL: OVF-B should be upstream"
    assert "OVF-E" in result_ids, "FAIL: OVF-E should be upstream"
    assert "OVF-F" in result_ids, "FAIL: OVF-F should be upstream"
    assert "OVF-D" not in result_ids, "FAIL: OVF-D is downstream, should not appear"
 
    dist_map = {r.overflow.id: r.river_distance_m for r in results}
    assert dist_map["OVF-A"] == 8000, f"FAIL: OVF-A distance should be 8000m, got {dist_map['OVF-A']}"
    assert dist_map["OVF-B"] == 3000, f"FAIL: OVF-B distance should be 3000m, got {dist_map['OVF-B']}"
    assert dist_map["OVF-E"] == 5000, f"FAIL: OVF-E distance should be 5000m, got {dist_map['OVF-E']}"
    assert dist_map["OVF-F"] == 11000, f"FAIL: OVF-F distance should be 11000m, got {dist_map['OVF-F']}"
 
    print("\n✅ All assertions passed.")
 
 
if __name__ == "__main__":
    run_poc_demo()
