"""
tests/test_upstream_query.py
 
Unit tests for the upstream traversal algorithm.
Run with: pytest tests/
"""
 
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
 
from graph.upstream_query import (
    build_graph_from_segments,
    find_upstream_nodes,
    query_upstream_overflows,
    plain_english_verdict,
    Overflow,
    UpstreamResult,
    _build_synthetic_network,
)
 
 
def test_upstream_nodes_main_stem():
    """Nodes on the main stem upstream of C should all be found."""
    G, _ = _build_synthetic_network()
    upstream = find_upstream_nodes(G, "C")
    assert "A" in upstream
    assert "B" in upstream
    assert "E" in upstream
    assert "F" in upstream
 
 
def test_downstream_node_not_upstream():
    """Node D is downstream of C — must not appear in upstream results."""
    G, _ = _build_synthetic_network()
    upstream = find_upstream_nodes(G, "C")
    assert "D" not in upstream
 
 
def test_distances():
    """Check accumulated distances are correct."""
    G, _ = _build_synthetic_network()
    upstream = find_upstream_nodes(G, "C")
    assert upstream["B"] == 3000, f"Expected 3000, got {upstream['B']}"
    assert upstream["A"] == 8000, f"Expected 8000, got {upstream['A']}"
    assert upstream["E"] == 5000, f"Expected 5000, got {upstream['E']}"
    assert upstream["F"] == 11000, f"Expected 11000, got {upstream['F']}"
 
 
def test_query_upstream_overflows_returns_correct_ids():
    G, overflows = _build_synthetic_network()
    results = query_upstream_overflows(52.00, 0.08, G, overflows)
    result_ids = {r.overflow.id for r in results}
    assert result_ids == {"OVF-A", "OVF-B", "OVF-E", "OVF-F"}
 
 
def test_query_upstream_overflows_sorted_by_distance():
    G, overflows = _build_synthetic_network()
    results = query_upstream_overflows(52.00, 0.08, G, overflows)
    distances = [r.river_distance_m for r in results]
    assert distances == sorted(distances)
 
 
def test_max_distance_filter():
    """With a 4km cap, only OVF-B (3km) should appear."""
    G, overflows = _build_synthetic_network()
    results = query_upstream_overflows(52.00, 0.08, G, overflows, max_distance_m=4000)
    result_ids = {r.overflow.id for r in results}
    assert result_ids == {"OVF-B"}
 
 
def test_plain_english_verdict_spilling():
    overflow = Overflow(id="X", name="X", lat=0, lon=0, status="spilling", snapped_node="A")
    results = [UpstreamResult(overflow=overflow, river_distance_m=3200)]
    verdict = plain_english_verdict(results)
    assert "spilling" in verdict.lower()
    assert "3.2" in verdict
 
 
def test_plain_english_verdict_empty():
    verdict = plain_english_verdict([])
    assert "no monitored" in verdict.lower()
