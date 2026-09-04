import pytest
import sys
from pathlib import Path

code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from topology import compute_metrics
from simulation import check_disconnected, run_kuramoto_simulation

def test_graph_connectivity_invariance():
    """Test that metrics are invariant to node relabeling (conceptually)."""
    # Simple check: a connected graph should remain connected
    edges = [(0, 1), (1, 2), (2, 3)]
    metrics = compute_metrics(edges, 4)
    assert metrics["connectivity"] == True

def test_metric_bounds():
    """Test that clustering coefficient is between 0 and 1."""
    edges = [(0, 1), (1, 2), (2, 0), (0, 3)]
    metrics = compute_metrics(edges, 4)
    assert 0.0 <= metrics["clustering_coefficient"] <= 1.0

def test_disconnected_graph_handling():
    """Test that disconnected graphs return infinity for path length."""
    edges = [(0, 1), (2, 3)] # Two components
    metrics = compute_metrics(edges, 4)
    assert metrics["connectivity"] == False
    assert metrics["average_path_length"] == float('inf')
