"""
graph/build_graph.py
 
Builds a directed NetworkX graph from river network geometries.
 
Each node is a point along the river (segment endpoint).
Each edge is a river segment, directed downstream (from -> to).
Edge weight = length in metres.
 
Phase 3 diagnostic will validate whether EA DRN carries reliable
flow-direction attributes. If yes, we use them directly. If not,
we derive direction from DEM elevation — the slower path.
 
Phase 4 will build this out for national coverage.
"""
 
# Placeholder — implementation in Phase 4
