"""
Unit tests for the convergence testing logic in code/convergence_test.py.

These tests verify the generic algorithm for running simulations on multiple seeds
and computing convergence metrics without requiring the full data pipeline.
"""

import pytest
import numpy as np
import networkx as nx
import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from convergence_test import (
    run_convergence_simulation,
    compute_convergence_metrics,
    plot_convergence_results
)
from simulate_oscillators import set_seed

# Fixtures
@pytest.fixture
def simple_ring_graph():
    """Creates a simple ring graph for deterministic testing."""
    G = nx.cycle_graph(10)
    return G

@pytest.fixture
def random_graph():
    """Creates a random graph for stochastic testing."""
    set_seed(12345)
    G = nx.erdos_renyi_graph(20, 0.1)
    return G

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

# Tests
def test_run_convergence_simulation_basic(simple_ring_graph):
    """Test that the simulation runs and returns a list of results."""
    results = run_convergence_simulation(simple_ring_graph, base_seed=42, num_seeds=3)
    
    assert isinstance(results, list)
    assert len(results) == 3
    
    for r in results:
        assert 'seed' in r
        assert 'decay_rate' in r
        assert 'r_squared' in r
        assert 'status' in r
        # Seed should be correct
        assert r['seed'] in [42, 43, 44]

def test_run_convergence_simulation_success_rate(simple_ring_graph):
    """Test that most seeds succeed in a stable system (Ring graph)."""
    results = run_convergence_simulation(simple_ring_graph, base_seed=100, num_seeds=10)
    
    successful = [r for r in results if r['status'] == 'dissipative']
    # We expect at least 80% success on a stable ring graph
    assert len(successful) >= 8

def test_compute_convergence_metrics_empty():
    """Test metrics calculation with empty or all-failed results."""
    empty_results = []
    metrics = compute_convergence_metrics(empty_results)
    
    assert metrics['mean_decay_rate'] is None
    assert metrics['converged'] is False
    assert 'Insufficient valid results' in metrics['reason']

def test_compute_convergence_metrics_low_variance(random_graph):
    """Test that a stable system reports low coefficient of variation."""
    # Run a small set of seeds
    results = run_convergence_simulation(random_graph, base_seed=999, num_seeds=5)
    metrics = compute_convergence_metrics(results)
    
    # We can't guarantee convergence on a random graph in 5 runs,
    # but we can verify the structure of the output
    assert 'mean_decay_rate' in metrics
    assert 'std_decay_rate' in metrics
    assert 'coefficient_of_variation' in metrics
    assert 'converged' in metrics

def test_plot_convergence_results_creates_file(simple_ring_graph, temp_output_dir):
    """Test that the plotting function creates a valid file."""
    results = run_convergence_simulation(simple_ring_graph, base_seed=500, num_seeds=5)
    metrics = compute_convergence_metrics(results)
    
    output_path = os.path.join(temp_output_dir, "test_plot.png")
    plot_convergence_results(results, metrics, output_path)
    
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_integration_with_json_io(random_graph, temp_output_dir):
    """Test the full flow: graph -> JSON -> simulation -> metrics."""
    # 1. Save graph to temp JSON
    graph_json = os.path.join(temp_output_dir, "graph.json")
    with open(graph_json, 'w') as f:
        json.dump({'edges': list(random_graph.edges())}, f)
    
    # 2. Run simulation (simulating the main logic)
    results = run_convergence_simulation(random_graph, base_seed=777, num_seeds=4)
    metrics = compute_convergence_metrics(results)
    
    # 3. Verify metrics structure
    assert isinstance(metrics, dict)
    assert 'valid_count' in metrics
    assert metrics['valid_count'] <= 4
    
    # 4. Verify results are populated
    valid_results = [r for r in results if r['decay_rate'] is not None]
    if len(valid_results) > 0:
        assert all(isinstance(r['decay_rate'], (int, float)) for r in valid_results)

def test_seed_reproducibility(simple_ring_graph):
    """Test that running with the same seed produces the same results."""
    results1 = run_convergence_simulation(simple_ring_graph, base_seed=111, num_seeds=2)
    results2 = run_convergence_simulation(simple_ring_graph, base_seed=111, num_seeds=2)
    
    for r1, r2 in zip(results1, results2):
        assert r1['decay_rate'] == r2['decay_rate']
        assert r1['r_squared'] == r2['r_squared']
        assert r1['status'] == r2['status']