"""
Unit tests for the public API in `code/structural.py`.

These tests verify that the high‑level wrapper functions provided in the
`code.structural` module correctly compute graph metrics and return the
expected keys:
  - global_efficiency
  - clustering
  - modularity

The tests also exercise the convenience helper `compute_subject_metrics`,
which loads a subject‑specific adjacency matrix from a ``.npy`` file,
computes the metrics, and returns a dictionary that includes the
``subject_id`` field.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Ensure the project root is on the import path so that `import structural`
# resolves to `code/structural.py`.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from structural import (
    calculate_graph_metrics,
    compute_subject_metrics,
)


def test_calculate_graph_metrics_returns_expected_keys():
    """
    Create a simple fully‑connected adjacency matrix (no self‑loops) and
    verify that the metric calculation returns the three required keys.
    """
    n = 5
    adj = np.ones((n, n))
    np.fill_diagonal(adj, 0.0)  # remove self‑loops

    metrics = calculate_graph_metrics(adj, density_threshold=1.0)

    # Expected keys
    expected_keys = {"global_efficiency", "clustering", "modularity"}
    assert set(metrics.keys()) == expected_keys, "Metric keys mismatch"

    # Basic sanity checks – all values should be positive and ≤ 1
    for key, value in metrics.items():
        assert isinstance(value, float), f"{key} should be a float"
        assert 0.0 <= value <= 1.0, f"{key} out of plausible range"


def test_compute_subject_metrics_loads_and_processes_file(tmp_path):
    """
    Write a temporary ``{subject_id}_matrix.npy`` file, invoke the helper,
    and confirm that the returned dictionary contains the subject ID and
    the three metric fields.
    """
    subject_id = "sub-TEST"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple adjacency matrix (complete graph)
    n = 4
    adj = np.ones((n, n))
    np.fill_diagonal(adj, 0.0)

    matrix_path = data_dir / f"{subject_id}_matrix.npy"
    np.save(matrix_path, adj)

    result = compute_subject_metrics(str(subject_id), str(data_dir), density_threshold=1.0)

    # Verify the result contains the expected fields
    assert result["subject_id"] == subject_id
    for key in ("global_efficiency", "clustering", "modularity"):
        assert key in result
        assert isinstance(result[key], float)
        assert 0.0 <= result[key] <= 1.0

    # The temporary file should have been read without error
    assert matrix_path.is_file()


def test_compute_subject_metrics_raises_when_file_missing(tmp_path):
    """
    Ensure that a missing ``.npy`` file triggers a ``FileNotFoundError``.
    """
    subject_id = "nonexistent"
    data_dir = tmp_path / "empty"
    data_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(FileNotFoundError):
        compute_subject_metrics(str(subject_id), str(data_dir), density_threshold=1.0)