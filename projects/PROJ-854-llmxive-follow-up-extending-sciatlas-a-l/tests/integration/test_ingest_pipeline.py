import os
import tempfile
import pytest
import pandas as pd
import networkx as nx
import sys
import logging

# Configure logging for the test run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adjust path to match project structure relative to this file
# The project root is assumed to be two levels up from tests/integration
_project_root = os.path.join(os.path.dirname(__file__), '..', '..', 'code')
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.services.ingest import fetch_and_build_subgraph
from src.lib import config
from src.models.node import Node

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger.info(f"Created temporary directory: {tmpdir}")
        yield tmpdir

def test_ingest_creates_subgraph(temp_output_dir):
    """
    Integration test for the ingestion pipeline on a sample of OpenAlex data.
    
    Verifies that:
    1. The fetch_and_build_subgraph function executes without error.
    2. It returns a valid networkx.Graph object.
    3. The graph contains at least one node and one edge.
    4. Nodes have the required attributes (id, title, citation_count, etc.).
    5. The output parquet file is created at the expected path.
    """
    # Configuration for a small sample to ensure fast execution
    # Targeting a small subgraph to avoid rate limits and long execution times
    sample_size = 20 
    output_path = os.path.join(temp_output_dir, "test_subgraph.parquet")
    
    logger.info(f"Running ingestion pipeline with target size: {sample_size}")
    logger.info(f"Output path: {output_path}")
    
    # Execute the ingestion pipeline
    # We pass a temporary directory for logs/data to avoid polluting the real data dir
    try:
        G, nodes_df = fetch_and_build_subgraph(
            target_size=sample_size,
            output_path=output_path,
            sample_seed=42
        )
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

    # Assertions
    assert isinstance(G, nx.Graph), "Output must be a networkx.Graph"
    assert G.number_of_nodes() > 0, "Graph must contain at least one node"
    assert G.number_of_edges() > 0, "Graph must contain at least one edge (sampled subgraph)"
    
    # Verify node attributes based on the Node dataclass and ingestion logic
    required_attrs = ['id', 'title', 'citation_count', 'embedding_vector', 'primary_cluster', 'topic_cluster']
    for node_id, data in G.nodes(data=True):
        for attr in required_attrs:
            assert attr in data, f"Node {node_id} missing '{attr}'"
        
        assert isinstance(data['citation_count'], (int, float)), "citation_count must be numeric"
        # embedding_vector is typically a list or numpy array
        assert data['embedding_vector'] is not None, f"Node {node_id} has None embedding_vector"
        
    # Verify DataFrame output
    assert isinstance(nodes_df, pd.DataFrame), "nodes_df must be a pandas DataFrame"
    assert len(nodes_df) == G.number_of_nodes(), "DataFrame row count must match graph node count"
    assert 'id' in nodes_df.columns, "DataFrame must have 'id' column"
    assert 'title' in nodes_df.columns, "DataFrame must have 'title' column"
    assert 'citation_count' in nodes_df.columns, "DataFrame must have 'citation_count' column"
    
    # Verify file creation
    assert os.path.exists(output_path), f"Output file not created at {output_path}"
    
    # Verify we can load the file back
    loaded_df = pd.read_parquet(output_path)
    assert len(loaded_df) == len(nodes_df), "Loaded DataFrame size mismatch"
    logger.info(f"Test passed: Subgraph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

def test_ingest_handles_empty_response(temp_output_dir):
    """
    Test that the pipeline handles cases where the sample size results in no valid nodes.
    This is an edge case check.
    """
    # We use a very small target size or a seed that might yield nothing in a real scenario,
    # but since we are testing the logic, we rely on the function's internal handling.
    # If the function returns an empty graph, it should still be a valid graph.
    output_path = os.path.join(temp_output_dir, "test_empty.parquet")
    
    # Note: In a real scenario with OpenAlex, a sample_size of 0 or 1 might behave differently.
    # We test the robustness of the return type.
    G, nodes_df = fetch_and_build_subgraph(
        target_size=1, # Minimal valid request
        output_path=output_path,
        sample_seed=12345
    )
    
    assert isinstance(G, nx.Graph)
    assert isinstance(nodes_df, pd.DataFrame)
    # Even if empty, the structure should be valid
    logger.info(f"Empty/minimal test passed: {G.number_of_nodes()} nodes.")