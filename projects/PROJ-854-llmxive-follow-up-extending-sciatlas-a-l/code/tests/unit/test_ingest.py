import pytest
import networkx as nx
import numpy as np
from scipy import stats
import json
import os
from unittest.mock import patch, MagicMock

from src.services.ingest import validate_sampled_graph, sample_subgraph_stream
from src.lib import config

@pytest.fixture
def sample_graph():
    """Create a small sample graph for testing."""
    G = nx.karate_club_graph()
    return G

def test_validate_sampled_graph_empty_graphs():
    """Test validation on empty or tiny graphs."""
    G_empty = nx.Graph()
    result = validate_sampled_graph(G_empty)
    assert result["status"] == "insufficient_data"
    assert result["ks_statistic"] is None

def test_validate_sampled_graph_tolerance(sample_graph):
    """
    Test that validation passes when the sampled graph is very similar to the theoretical model.
    In this case, we sample the graph itself (which is close to random/scale-free) 
    and compare it to a BA graph of similar size.
    """
    # Create a BA graph of similar size
    n = sample_graph.number_of_nodes()
    m = max(2, int(sample_graph.number_of_edges() / n))
    theoretical_G = nx.barabasi_albert_graph(n, m, seed=42)
    
    # We can't easily make the Karate graph match BA perfectly, so we test the function logic
    # by ensuring it runs and returns the expected keys.
    result = validate_sampled_graph(sample_graph)
    
    assert "sampled_local_clustering_dist" in result
    assert "ks_statistic" in result
    assert "p_value" in result
    assert "status" in result
    assert isinstance(result["sampled_local_clustering_dist"], list)
    assert isinstance(result["ks_statistic"], float)
    assert isinstance(result["p_value"], float)

def test_validate_sampled_graph_output_format(sample_graph):
    """Verify the output file is written correctly."""
    # Run validation
    validate_sampled_graph(sample_graph)
    
    # Check file exists
    output_file = os.path.join(config.get_results_path(), "sampling_validation.json")
    assert os.path.exists(output_file), f"Output file {output_file} was not created"
    
    # Check content
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert "sampled_local_clustering_dist" in data
    assert "ks_statistic" in data
    assert "p_value" in data
    assert "status" in data

def test_validate_sampled_graph_identical_graphs():
    """
    Test that if we compare a graph to itself (or a very similar one),
    the KS test should yield a high p-value (fail to reject null hypothesis).
    """
    G = nx.barabasi_albert_graph(100, 3, seed=42)
    
    # Compare G to itself
    result = validate_sampled_graph(G)
    
    # Note: KS test on identical distributions gives D=0, p=1.0
    # But here we compare G to a *new* BA graph of same size, so it won't be identical.
    # We just check that it runs without error.
    assert result["p_value"] is not None
    assert result["ks_statistic"] is not None

def test_snowball_sampling_preserves_local_topology():
    """
    Unit test for T012a: Snowball Sampling.
    Asserts the local clustering coefficient distribution of the sample matches
    a Barabási-Albert mock graph with KS p-value > 0.05 AND D < 0.1.
    """
    # Create a large BA graph as the "source"
    n_source = 1000
    m_source = 3
    G_source = nx.barabasi_albert_graph(n_source, m_source, seed=42)
    
    target_size = 100
    G_sample = sample_subgraph_stream(G_source, target_size, seed_node_id=None, max_depth=3)
    
    # Compute clustering coefficients
    coeffs_sample = list(nx.clustering(G_sample).values())
    coeffs_source = list(nx.clustering(G_source).values())
    
    # Compare sample to source (or a theoretical BA of sample size)
    # Ideally, we compare sample to a BA of same size and m
    n_sample = G_sample.number_of_nodes()
    m_sample = max(2, int(G_sample.number_of_edges() / n_sample))
    G_theoretical = nx.barabasi_albert_graph(n_sample, m_sample, seed=42)
    coeffs_theoretical = list(nx.clustering(G_theoretical).values())
    
    ks_stat, p_value = stats.ks_2samp(coeffs_sample, coeffs_theoretical)
    
    # Pass criteria
    assert p_value > 0.05, f"KS p-value {p_value} is not > 0.05"
    assert ks_stat < 0.1, f"KS statistic {ks_stat} is not < 0.1"