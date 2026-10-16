"""
Unit tests for the graph_builder module.

These tests verify that graph metrics are correctly computed for both
connected and disconnected coupling maps and that the CSV generation
produces a non‑empty file with the expected schema.
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.graph_builder import (
    build_coupling_graph,
    compute_shortest_path_metrics,
    compute_clustering_and_assortativity,
    compute_edge_betweenness_and_spectral_gap,
    process_device_coupling_map,
    generate_graph_metrics_csv,
)


def test_build_coupling_graph_path():
    """A simple 3‑node path graph should yield correct basic metrics."""
    coupling_map = [[0, 1], [1, 2]]
    G = build_coupling_graph(coupling_map)

    # shortest‑path metrics
    sp_metrics = compute_shortest_path_metrics(G)
    # distances: 0‑1=1, 0‑2=2, 1‑2=1 → avg = 4/3
    assert pytest.approx(sp_metrics["avg_shortest_path"], 0.01) == 4 / 3
    assert sp_metrics["diameter"] == 2

    # clustering & assortativity (no triangles → clustering 0)
    ca_metrics = compute_clustering_and_assortativity(G)
    assert ca_metrics["clustering_coeff"] == pytest.approx(0.0, 1e-6)
    # degree assortativity for a path of length 2 is -0.5
    assert ca_metrics["assortativity"] == pytest.approx(-0.5, 0.01)

    # edge betweenness and spectral gap
    eb_sg = compute_edge_betweenness_and_spectral_gap(G)
    # each edge lies on the unique shortest path between the non‑adjacent nodes,
    # so edge betweenness = 1 for both edges → mean = 1
    assert eb_sg["edge_betweenness_mean"] == pytest.approx(1.0, 1e-6)
    # spectral gap must be > 0 for a connected graph
    assert eb_sg["spectral_gap"] > 0.0


def test_build_coupling_graph_disconnected():
    """A graph with two separate components must have spectral gap = 0."""
    # Two independent edges → two connected components
    coupling_map = [[0, 1], [2, 3]]
    G = build_coupling_graph(coupling_map)

    # shortest‑path metrics are computed on the largest component (size 2)
    sp_metrics = compute_shortest_path_metrics(G)
    assert sp_metrics["avg_shortest_path"] == pytest.approx(1.0, 1e-6)
    assert sp_metrics["diameter"] == 1

    # spectral gap should be exactly 0 for a disconnected graph
    eb_sg = compute_edge_betweenness_and_spectral_gap(G)
    assert eb_sg["spectral_gap"] == pytest.approx(0.0, 1e-6)


def test_generate_graph_metrics_csv(tmp_path: Path):
    """The CSV generator must write at least one metric row per device."""
    # Create a temporary raw data directory with a single JSON snapshot
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)

    snapshot = {
        "device_id": "test_device",
        "timestamp": "2024-01-01T00:00:00Z",
        "coupling_map": [[0, 1], [1, 2]]
    }
    json_path = raw_dir / "test_device_20240101.json"
    json_path.write_text(json.dumps(snapshot))

    output_csv = tmp_path / "graph_metrics.csv"

    # Run the generator
    generate_graph_metrics_csv(str(raw_dir), str(output_csv))

    # Verify the CSV exists and contains rows
    assert output_csv.is_file()
    df = pd.read_csv(output_csv)

    # Expected columns per schema
    expected_cols = {"device_id", "metric_name", "value", "is_finite"}
    assert set(df.columns) == expected_cols

    # At least one metric per device should be present
    assert not df.empty
    assert (df["device_id"] == "test_device").all()