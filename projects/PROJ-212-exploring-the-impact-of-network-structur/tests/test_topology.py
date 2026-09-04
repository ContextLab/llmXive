import pytest
import sys
from pathlib import Path

code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from topology import compute_metrics

def test_degree_distribution():
    """Test degree distribution calculation."""
    # Star graph: center node degree 4, leaves degree 1
    edges = [(0, 1), (0, 2), (0, 3), (0, 4)]
    metrics = compute_metrics(edges, 5)
    assert metrics["degree_mean"] == 1.6 # (4 + 1 + 1 + 1 + 1) / 5
    assert metrics["degree_std"] > 0

def test_clustering_coefficient():
    """Test clustering coefficient calculation."""
    # Triangle: clustering should be 1.0
    edges = [(0, 1), (1, 2), (2, 0)]
    metrics = compute_metrics(edges, 3)
    assert abs(metrics["clustering_coefficient"] - 1.0) < 0.01

def test_average_path_length():
    """Test average path length calculation."""
    # Line graph: 0-1-2-3
    edges = [(0, 1), (1, 2), (2, 3)]
    metrics = compute_metrics(edges, 4)
    # Path lengths: 1, 2, 3, 1, 2, 1 -> avg = 9/6 = 1.5
    assert abs(metrics["average_path_length"] - 1.5) < 0.01
