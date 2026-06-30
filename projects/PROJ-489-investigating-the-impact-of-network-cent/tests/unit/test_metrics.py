import pytest
import numpy as np
import pandas as pd
import networkx as nx
from metrics import aggregate_pli_to_global, calculate_vif, compute_centralities, compute_pli

def test_aggregate_pli_to_global_numpy():
    """Test aggregation of 3D numpy array to global synchrony scores."""
    n_subjects = 5
    n_stages = 3
    n_pairs = 10
    sleep_stages = ['Wake', 'N2', 'REM']
    
    # Create dummy data
    data = np.ones((n_subjects, n_stages, n_pairs))
    # Make values distinct per stage to verify averaging
    data[:, 0, :] = 0.5  # Wake
    data[:, 1, :] = 0.8  # N2
    data[:, 2, :] = 0.2  # REM
    
    result = aggregate_pli_to_global(data, sleep_stages)
    
    assert isinstance(result, pd.DataFrame)
    assert 'subject_id' in result.columns
    for stage in sleep_stages:
        assert stage in result.columns
        
    # Check values
    assert np.allclose(result['Wake'], 0.5)
    assert np.allclose(result['N2'], 0.8)
    assert np.allclose(result['REM'], 0.2)

def test_aggregate_pli_to_global_dataframe():
    """Test aggregation from long-format DataFrame."""
    data = {
        'subject_id': [1, 1, 1, 2, 2, 2],
        'stage': ['Wake', 'N2', 'REM', 'Wake', 'N2', 'REM'],
        'pli_value': [0.5, 0.8, 0.2, 0.6, 0.9, 0.3]
    }
    df = pd.DataFrame(data)
    
    result = aggregate_pli_to_global(df, ['Wake', 'N2', 'REM'])
    
    assert isinstance(result, pd.DataFrame)
    assert 'subject_id' in result.columns
    assert 'Wake' in result.columns
    assert result.loc[result['subject_id'] == 1, 'Wake'].values[0] == 0.5
    assert result.loc[result['subject_id'] == 2, 'Wake'].values[0] == 0.6

def test_calculate_vif():
    """Test VIF calculation."""
    data = {
        'degree': [1.0, 2.0, 3.0, 4.0, 5.0],
        'betweenness': [1.0, 2.0, 3.0, 4.0, 5.0], # Perfectly collinear for testing
        'eigenvector': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    # This will likely result in high VIF due to perfect collinearity
    vif = calculate_vif(df, ['degree', 'betweenness', 'eigenvector'])
    
    assert len(vif) == 3
    assert vif['degree'] > 1.0 # Should be high

def test_aggregate_invalid_input():
    """Test error handling for invalid input types."""
    with pytest.raises(TypeError):
        aggregate_pli_to_global("invalid", ['A', 'B'])
        
    with pytest.raises(ValueError):
        # 2D array should raise error in our logic if not handled as DataFrame
        aggregate_pli_to_global(np.ones((5, 5)), ['A', 'B'])

def test_compute_centralities_synthetic_graph():
    """
    Unit test for NetworkX centrality calculation on a synthetic graph.
    Verifies degree, betweenness, and eigenvector centrality logic.
    """
    # Construct a synthetic graph: a central hub connected to 4 leaves
    # Graph structure: 0 is connected to 1, 2, 3, 4
    G = nx.Graph()
    G.add_edges_from([
        (0, 1), (0, 2), (0, 3), (0, 4)
    ])
    
    # Call the function under test
    centralities = compute_centralities(G)
    
    # Verify return type
    assert isinstance(centralities, dict)
    assert 'degree' in centralities
    assert 'betweenness' in centralities
    assert 'eigenvector' in centralities
    
    # Verify specific values for the star graph
    # Node 0 (hub): degree should be 4
    assert centralities['degree'][0] == 4.0
    
    # Node 0 (hub): betweenness should be high (all paths go through it)
    # In a star graph with 5 nodes, betweenness for center is 1.0 (normalized)
    # or close to it depending on normalization.
    assert centralities['betweenness'][0] > 0.5
    
    # Nodes 1-4 (leaves): degree should be 1
    for i in range(1, 5):
        assert centralities['degree'][i] == 1.0
        assert centralities['betweenness'][i] == 0.0
    
    # Eigenvector centrality: hub should have higher score than leaves
    assert centralities['eigenvector'][0] > centralities['eigenvector'][1]

def test_compute_centralities_empty_graph():
    """Test centrality calculation on an empty graph."""
    G = nx.Graph()
    G.add_nodes_from([1, 2, 3])
    
    centralities = compute_centralities(G)
    
    assert isinstance(centralities, dict)
    # All centralities should be 0 for disconnected nodes
    assert centralities['degree'][1] == 0.0
    assert centralities['betweenness'][1] == 0.0
    # Eigenvector might be 0 or very small depending on implementation
    assert centralities['eigenvector'][1] == 0.0

def test_compute_centralities_single_node():
    """Test centrality calculation on a single node graph."""
    G = nx.Graph()
    G.add_node(1)
    
    centralities = compute_centralities(G)
    
    assert centralities['degree'][1] == 0.0
    assert centralities['betweenness'][1] == 0.0
    assert centralities['eigenvector'][1] == 0.0

def test_compute_pli_synthetic_signal():
    """
    Unit test for Phase Lag Index (PLI) calculation on synthetic signals.
    Verifies that PLI correctly identifies synchrony and asynchrony.
    """
    rng = np.random.default_rng(42)
    n_samples = 1000
    fs = 256.0
    t = np.linspace(0, n_samples / fs, n_samples)
    
    # Scenario 1: Perfectly synchronized signals (phase difference = 0)
    # Two sine waves with same phase
    signal_a_sync = np.sin(2 * np.pi * 10 * t)
    signal_b_sync = np.sin(2 * np.pi * 10 * t)
    
    pli_sync = compute_pli(signal_a_sync, signal_b_sync, fs, band='alpha')
    
    # PLI should be close to 1.0 for perfectly synchronized signals
    assert 0.9 <= pli_sync <= 1.0, f"Expected PLI ~1.0 for synchronized signals, got {pli_sync}"
    
    # Scenario 2: Anti-phase signals (phase difference = pi)
    # One sine wave, one inverted
    signal_b_anti = -np.sin(2 * np.pi * 10 * t)
    
    pli_anti = compute_pli(signal_a_sync, signal_b_anti, fs, band='alpha')
    
    # PLI should be close to 1.0 for anti-phase signals (consistent lag)
    assert 0.9 <= pli_anti <= 1.0, f"Expected PLI ~1.0 for anti-phase signals, got {pli_anti}"
    
    # Scenario 3: Random phase difference (no consistent lag)
    # Add random phase shift to each sample (or use noise)
    noise_a = rng.normal(0, 1, n_samples)
    noise_b = rng.normal(0, 1, n_samples)
    
    pli_noise = compute_pli(noise_a, noise_b, fs, band='alpha')
    
    # PLI should be close to 0.0 for random noise (no consistent phase lag)
    assert pli_noise < 0.3, f"Expected PLI < 0.3 for random noise, got {pli_noise}"
    
    # Scenario 4: 90-degree phase shift (quadrature)
    # This creates a consistent lag of pi/2
    signal_b_quad = np.sin(2 * np.pi * 10 * t + np.pi / 2)
    
    pli_quad = compute_pli(signal_a_sync, signal_b_quad, fs, band='alpha')
    
    # PLI should be close to 1.0 for consistent phase lag
    assert 0.8 <= pli_quad <= 1.0, f"Expected PLI > 0.8 for consistent phase lag, got {pli_quad}"

def test_compute_pli_invalid_inputs():
    """Test PLI calculation with invalid inputs."""
    rng = np.random.default_rng(42)
    signal_a = rng.normal(0, 1, 100)
    signal_b = rng.normal(0, 1, 100)
    
    # Test with mismatched lengths
    signal_b_short = rng.normal(0, 1, 50)
    with pytest.raises(ValueError):
        compute_pli(signal_a, signal_b_short, 256.0, band='alpha')
    
    # Test with empty arrays
    with pytest.raises(ValueError):
        compute_pli(np.array([]), np.array([]), 256.0, band='alpha')
    
    # Test with invalid band
    with pytest.raises(ValueError):
        compute_pli(signal_a, signal_b, 256.0, band='invalid_band')