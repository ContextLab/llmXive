import pytest
import networkx as nx
import pandas as pd
import os
import tempfile
from src.models.graph_utils import calc_bridging, louvain_cluster

def test_calc_bridging_complete_graph():
    """
    In a complete graph, every node is connected to every other node.
    If all nodes are in the same cluster, bridging should be 0.
    If nodes are in different clusters, bridging depends on cluster split.
    """
    G = nx.complete_graph(5)
    # All in same cluster
    clusters = {i: 0 for i in range(5)}
    calc_bridging(G, clusters)
    for node in G.nodes():
        assert G.nodes[node]['bridging_coefficient'] == 0.0

def test_calc_bridging_bipartite_clusters():
    """
    Bipartite graph: 0-1, 2-3, 4-5. Clusters: {0,1,2,3} and {4,5}.
    Node 0 connected to 1,2,3. All in same cluster -> bridging 0.
    Node 4 connected to 5. Same cluster -> bridging 0.
    Let's make a graph where inter-cluster edges exist.
    Graph: 0-1, 1-2, 2-3. Clusters: {0,1}, {2,3}.
    Node 1: neighbors 0 (same), 2 (diff). Degree 2. Inter=1. Bridging=0.5.
    """
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2), (2, 3)])
    clusters = {0: 0, 1: 0, 2: 1, 3: 1}
    calc_bridging(G, clusters)
    
    # Node 1: degree 2, inter=1 (to 2) -> 0.5
    assert G.nodes[1]['bridging_coefficient'] == 0.5
    # Node 0: degree 1, inter=0 -> 0.0
    assert G.nodes[0]['bridging_coefficient'] == 0.0

def test_isolated_node():
    """
    Isolated node (degree 0) should have bridging 0.0.
    """
    G = nx.Graph()
    G.add_node(1)
    clusters = {1: 0}
    calc_bridging(G, clusters)
    assert G.nodes[1]['bridging_coefficient'] == 0.0

def test_single_node_cluster():
    """
    Single node cluster in a larger graph.
    """
    G = nx.Graph()
    G.add_edges_from([(0, 1), (1, 2)])
    clusters = {0: 0, 1: 1, 2: 0}
    calc_bridging(G, clusters)
    # Node 1: neighbors 0 (diff), 2 (diff). Degree 2. Inter=2. Bridging=1.0.
    assert G.nodes[1]['bridging_coefficient'] == 1.0

def test_calc_bridging_missing_cluster_assignment():
    """
    Node without cluster assignment should get 0.0.
    """
    G = nx.Graph()
    G.add_edge(0, 1)
    clusters = {0: 0} # 1 is missing
    calc_bridging(G, clusters)
    # Node 0: neighbor 1 (missing cluster). Inter=0?
    # Logic: if neighbor_cluster is None, continue. So inter=0.
    assert G.nodes[0]['bridging_coefficient'] == 0.0
    # Node 1: no cluster.
    assert G.nodes[1]['bridging_coefficient'] == 0.0

def verify_parquet():
    """
    T016a: Verify saved graph artifact.
    Checks existence and columns.
    """
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))
    from src.lib import config
    
    output_path = config.get_processed_data_path() / "subgraph_with_clusters.parquet"
    
    if not os.path.exists(output_path):
        pytest.skip(f"File {output_path} does not exist. Run the pipeline first.")
    
    df = pd.read_parquet(output_path)
    required_cols = ['id', 'title', 'citation_count', 'primary_cluster', 'bridging_coefficient']
    
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check for nulls in primary_cluster for nodes with degree > 0 (if we had degree info)
    # Since we don't have degree in df, we check generally.
    # T016a: Assert primary_cluster has no nulls for nodes with degree > 0.
    # We can't verify degree here without the graph, so we check no nulls at all?
    # Or assume the pipeline handles it.
    # Let's assert no nulls in primary_cluster.
    assert df['primary_cluster'].notnull().all(), "primary_cluster has nulls."
    
    # Assert bridging_coefficient is non-null
    assert df['bridging_coefficient'].notnull().all(), "bridging_coefficient has nulls."

def test_verify_parquet():
    """
    Wrapper for pytest.
    """
    verify_parquet()
