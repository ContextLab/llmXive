import os
import sys
import pytest
import pandas as pd
import networkx as nx
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.splits import (
    load_raw_flows,
    create_temporal_split,
    build_graph_from_train_flows,
    validate_no_leakage,
    save_splits,
    save_graph
)

@pytest.fixture
def sample_flows():
    """Create sample flow data with timestamps."""
    data = {
        'src_ip': ['192.168.1.1', '192.168.1.2', '192.168.1.1', '192.168.1.3', '192.168.1.2'],
        'dst_ip': ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.1', '10.0.0.4'],
        'timestamp': [
            '2023-01-01 10:00:00',
            '2023-01-01 11:00:00',
            '2023-01-02 10:00:00',
            '2023-01-03 10:00:00',
            '2023-01-04 10:00:00'
        ],
        'bytes': [100, 200, 150, 300, 250]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_raw_dir(sample_flows):
    """Create a temporary directory with sample CSV file."""
    tmpdir = tempfile.mkdtemp()
    csv_path = os.path.join(tmpdir, 'test_flows.csv')
    sample_flows.to_csv(csv_path, index=False)
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_create_temporal_split(sample_flows):
    train_df, test_df = create_temporal_split(sample_flows, 0.6, seed=42)
    # 5 rows, 60% = 3 train, 2 test
    assert len(train_df) == 3
    assert len(test_df) == 2
    # Ensure train is earlier than test
    assert train_df['timestamp'].max() <= test_df['timestamp'].min()

def test_build_graph_from_train_flows(sample_flows):
    train_df, _ = create_temporal_split(sample_flows, 0.6, seed=42)
    G = build_graph_from_train_flows(train_df)
    assert G.number_of_nodes() > 0
    assert G.number_of_edges() > 0
    assert nx.is_directed(G)

def test_validate_no_leakage_no_leak(sample_flows):
    train_df, test_df = create_temporal_split(sample_flows, 0.6, seed=42)
    G = build_graph_from_train_flows(train_df)
    # All nodes in train are also in test (shared), so no "test-only" nodes
    assert validate_no_leakage(train_df, test_df, G) is True

def test_validate_no_leakage_with_leakage():
    """Create a scenario where test has a node not in train."""
    data = {
        'src_ip': ['192.168.1.1', '192.168.1.2', '192.168.1.1', '192.168.1.3'],
        'dst_ip': ['10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.5'],  # 10.0.0.5 only in test
        'timestamp': [
            '2023-01-01 10:00:00',
            '2023-01-01 11:00:00',
            '2023-01-02 10:00:00',
            '2023-01-03 10:00:00'
        ],
        'bytes': [100, 200, 150, 300]
    }
    df = pd.DataFrame(data)
    train_df, test_df = create_temporal_split(df, 0.5, seed=42)
    G = build_graph_from_train_flows(train_df)
    # Add an edge from train to a node that only appears in test (simulating leakage)
    # But our build_graph_from_train_flows only uses train data, so we must simulate a graph that has leakage
    # Instead, let's construct a graph that has an edge to a test-only node
    G_leaky = nx.DiGraph()
    G_leaky.add_edge('192.168.1.1', '10.0.0.5')  # 10.0.0.5 is in test only
    assert validate_no_leakage(train_df, test_df, G_leaky) is False

def test_save_splits_and_graph(sample_flows, temp_raw_dir):
    train_df, test_df = create_temporal_split(sample_flows, 0.6, seed=42)
    tmp_out = tempfile.mkdtemp()
    try:
        save_splits(train_df, test_df, tmp_out)
        assert os.path.exists(os.path.join(tmp_out, 'train_split.csv'))
        assert os.path.exists(os.path.join(tmp_out, 'test_split.csv'))

        G = build_graph_from_train_flows(train_df)
        graph_path = os.path.join(tmp_out, 'test_graph.graphml')
        save_graph(G, graph_path)
        assert os.path.exists(graph_path)
    finally:
        shutil.rmtree(tmp_out)
