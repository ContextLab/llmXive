import os
import sys
import tempfile
import pytest
import pandas as pd
import networkx as nx

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from data.preprocess import build_graph_from_csv, validate_graph
from utils.memory_monitor import start_monitoring, stop_monitoring, get_peak_memory_mb

@pytest.fixture
def sample_flows():
    """Create sample flow data for testing."""
    data = {
        "src_ip": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
        "dst_ip": ["192.168.1.2", "192.168.1.3", "192.168.1.1"],
        "packet_count": [100, 200, 150],
        "timestamp": [1000, 1001, 1002],
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_parquet_path(sample_flows):
    """Create a temporary parquet file with sample flows."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        sample_flows.to_parquet(f.name)
        yield f.name
        os.unlink(f.name)

def test_graph_construction_creates_nodes_and_edges(temp_parquet_path):
    """Test that graph construction creates correct nodes and edges."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_graph.graphml")
        scenario_name = "test"

        graph_path, peak_memory = build_graph_from_csv(
            temp_parquet_path, output_path, scenario_name
        )

        # Verify file exists
        assert os.path.exists(graph_path)

        # Load and verify graph
        G = nx.read_graphml(graph_path)

        # Should have 3 nodes
        assert G.number_of_nodes() == 3

        # Should have 3 edges
        assert G.number_of_edges() == 3

        # Check node properties
        for node in G.nodes():
            assert G.nodes[node].get("type") == "ip"

        # Check edge weights
        assert G["192.168.1.1"]["192.168.1.2"]["weight"] == 100.0
        assert G["192.168.1.2"]["192.168.1.3"]["weight"] == 200.0
        assert G["192.168.1.3"]["192.168.1.1"]["weight"] == 150.0

def test_graph_construction_handles_duplicate_edges(temp_parquet_path):
    """Test that duplicate edges accumulate weights."""
    # Add duplicate flow
    data = {
        "src_ip": ["192.168.1.1", "192.168.1.1", "192.168.1.2"],
        "dst_ip": ["192.168.1.2", "192.168.1.2", "192.168.1.3"],
        "packet_count": [100, 50, 200],
        "timestamp": [1000, 1001, 1002],
    }
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        df.to_parquet(f.name)
        temp_path = f.name

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_graph.graphml")
            scenario_name = "test"

            graph_path, _ = build_graph_from_csv(
                temp_path, output_path, scenario_name
            )

            G = nx.read_graphml(graph_path)

            # Edge should have accumulated weight
            assert G["192.168.1.1"]["192.168.1.2"]["weight"] == 150.0
    finally:
        os.unlink(temp_path)

def test_graph_construction_memory_limit():
    """Test that memory limit is enforced."""
    # Create a small dataset
    data = {
        "src_ip": ["192.168.1.1"],
        "dst_ip": ["192.168.1.2"],
        "packet_count": [100],
        "timestamp": [1000],
    }
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        df.to_parquet(f.name)
        temp_path = f.name

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_graph.graphml")

            # Set a very low memory limit (should not be exceeded for small data)
            graph_path, peak_memory = build_graph_from_csv(
                temp_path, output_path, "test", max_memory_gb=0.001
            )

            # For small data, this should succeed
            assert os.path.exists(graph_path)
    finally:
        os.unlink(temp_path)

def test_validate_graph_node_limit():
    """Test graph validation with node count limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a small graph
        G = nx.DiGraph()
        G.add_edges_from([("A", "B"), ("B", "C")])
        graph_path = os.path.join(tmpdir, "small.graphml")
        nx.write_graphml(G, graph_path)

        # Validate with high limit - should pass
        result = validate_graph(graph_path, max_nodes=100)
        assert result["is_valid"] is True
        assert len(result["warnings"]) == 0

        # Validate with low limit - should fail
        result = validate_graph(graph_path, max_nodes=1)
        assert result["is_valid"] is False
        assert len(result["warnings"]) > 0

def test_missing_input_file():
    """Test that missing input file raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test.graphml")

        with pytest.raises(FileNotFoundError):
            build_graph_from_csv(
                "nonexistent.parquet", output_path, "test"
            )

def test_missing_required_columns():
    """Test that missing columns raise error."""
    data = {
        "src_ip": ["192.168.1.1"],
        "dst_ip": ["192.168.1.2"],
        # Missing packet_count and timestamp
    }
    df = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        df.to_parquet(f.name)
        temp_path = f.name

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.graphml")

            with pytest.raises(ValueError):
                build_graph_from_csv(temp_path, output_path, "test")
    finally:
        os.unlink(temp_path)
