import os
import tempfile

import networkx as nx
import pytest

from generate_networks import compute_topological_metrics, save_metrics_to_csv, generate_random_graph

@pytest.mark.parametrize(
    "graph_factory",
    [
        lambda: nx.path_graph(5),
        lambda: nx.complete_graph(4),
        lambda: nx.cycle_graph(6),
    ],
)
def test_compute_topological_metrics_returns_expected_keys(graph_factory):
    """
    Verify that the metric extraction function returns a dictionary with
    all required keys and that each value is a float.
    """
    G = graph_factory()
    metrics = compute_topological_metrics(G)

    expected_keys = {
        "clustering_coeff",
        "degree_variance",
        "spectral_gap",
        "average_betweenness",
    }
    assert set(metrics.keys()) == expected_keys
    for key in expected_keys:
        assert isinstance(metrics[key], float)

def test_save_metrics_to_csv_creates_file_and_appends():
    """
    Ensure that the CSV writer creates a file with a header on first write
    and appends subsequent rows without duplicating the header.
    """
    G = nx.path_graph(5)
    metrics = compute_topological_metrics(G)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "metrics.csv")

        # First write – file should be created with header
        save_metrics_to_csv(metrics, csv_path, overwrite=False)
        assert os.path.isfile(csv_path)

        # Capture the number of lines after first write
        with open(csv_path, "r") as f:
            lines_first = f.readlines()
        assert len(lines_first) == 2  # header + one data row

        # Second write – should append a new row, header unchanged
        save_metrics_to_csv(metrics, csv_path, overwrite=False)
        with open(csv_path, "r") as f:
            lines_second = f.readlines()
        assert len(lines_second) == 3  # header + two data rows
        # Header line should be identical
        assert lines_first[0] == lines_second[0]

def test_generate_random_graph_and_metric_extraction():
    """
    Integration sanity check: generate a small Erdős‑Rényi graph using the
    provided random graph generator and compute metrics on it.
    """
    # Use a deterministic seed for reproducibility
    import numpy as np
    np.random.seed(42)

    G = generate_random_graph(num_nodes=10, edge_prob=0.3, seed=42)
    assert isinstance(G, nx.Graph)
    # The graph should have at least one edge for a meaningful metric set
    assert G.number_of_edges() > 0

    metrics = compute_topological_metrics(G)
    # Basic sanity – metrics dict should be non‑empty and contain floats
    for value in metrics.values():
        assert isinstance(value, float)