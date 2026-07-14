"""Unit tests for the graph‑metric computation utilities."""

import pathlib

import numpy as np
import pandas as pd
import pytest

from code import utils
from code.utils import graph as gutils

# Simple synthetic adjacency matrix (90 nodes not required for the test)
@pytest.fixture
def small_adj():
    # Create a 4‑node ring graph adjacency matrix
    mat = np.zeros((4, 4))
    for i in range(4):
        mat[i, (i + 1) % 4] = 1
        mat[(i + 1) % 4, i] = 1
    return mat

def test_compute_subject_metrics(small_adj):
    """Validate that compute_subject_metrics returns sensible numbers."""
    # The function lives in the script we just implemented.
    from code import _03_compute_graph_metrics as gm
    
    metrics = gm.compute_subject_metrics(small_adj)
    # For a ring of 4 nodes:
    # - degree of each node = 2 → mean = 2
    # - global efficiency for a regular ring ≈ 0.5
    # - clustering coefficient = 0 for a ring
    # - average shortest path length = 1.33...
    assert pytest.approx(metrics["degree_mean"], rel=1e-2) == 2.0
    assert 0.4 < metrics["global_efficiency"] < 0.6
    assert metrics["clustering_coeff_mean"] == 0.0
    assert pytest.approx(metrics["path_length_mean"], rel=1e-2) == 1.3333333
    
def test_write_and_load_csv(tmp_path: pathlib.Path):
    """Round‑trip test for the CSV helpers."""
    out_file = tmp_path / "metrics.csv"
    rows = [
        {
            "subject_id": "sub-01",
            "degree_mean": 2.0,
            "global_efficiency": 0.5,
            "clustering_coeff_mean": 0.0,
            "path_length_mean": 1.33,
        }
    ]
    utils.io.save_csv(out_file, rows)
    df = utils.io.load_csv(out_file)
    assert df.iloc[0]["subject_id"] == "sub-01"
    assert df.iloc[0]["degree_mean"] == 2.0

# The test suite is optional; it will be discovered by pytest if present.