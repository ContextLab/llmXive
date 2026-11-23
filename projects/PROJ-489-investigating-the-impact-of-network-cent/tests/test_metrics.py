"""
Unit tests for the metrics module (T003).
These tests verify that the core computational functions behave as expected
on synthetic data. Real EEG data is not required for the unit‑test suite.
"""

import numpy as np
import pandas as pd
import mne
import networkx as nx
import pytest

from metrics import (
    compute_connectivity_matrix,
    compute_centrality_metrics,
    compute_pli,
    calculate_vif,
    aggregate_subject_metrics,
)

# ----------------------------------------------------------------------
# Helper to create a minimal MNE Raw object with synthetic EEG data
# ----------------------------------------------------------------------
def _make_fake_raw(n_channels: int = 5, sfreq: float = 100.0, n_seconds: int = 10) -> mne.io.RawArray:
    """Create a RawArray containing random data (zero‑mean Gaussian)."""
    rng = np.random.default_rng(0)
    data = rng.normal(size=(n_channels, int(sfreq * n_seconds)))
    info = mne.create_info(ch_names=[f"EEG{i}" for i in range(n_channels)], sfreq=sfreq, ch_types="eeg")
    return mne.io.RawArray(data, info)

# ----------------------------------------------------------------------
# Test connectivity matrix generation
# ----------------------------------------------------------------------
def test_compute_connectivity_matrix_symmetry_and_range():
    raw = _make_fake_raw()
    conn_dict = compute_connectivity_matrix(raw, bands={"theta": (4, 8)})
    assert "theta" in conn_dict
    mat = conn_dict["theta"]
    # Symmetry
    assert np.allclose(mat, mat.T, atol=1e-8)
    # Values in (0, 1)
    assert np.all(mat >= 0) and np.all(mat <= 1)
    # Diagonal should be exactly 1
    assert np.allclose(np.diag(mat), 1.0)

# ----------------------------------------------------------------------
# Test centrality on a star graph (known reference values)
# ----------------------------------------------------------------------
def test_compute_centrality_metrics_star_graph():
    # Build star graph adjacency matrix (5 nodes, node 0 is hub)
    n = 5
    adj = np.zeros((n, n))
    for i in range(1, n):
        adj[0, i] = adj[i, 0] = 1.0
    # Compute centralities
    cent = compute_centrality_metrics(adj)

    # Expected degree centrality: hub 1.0, leaves 0.25 (since degree centrality = deg/(n-1))
    expected_degree = np.array([1.0] + [0.25] * (n - 1))
    np.testing.assert_allclose(cent["degree"], expected_degree, atol=1e-6)

    # Expected betweenness: hub 1.0, leaves 0.0
    expected_betweenness = np.array([1.0] + [0.0] * (n - 1))
    np.testing.assert_allclose(cent["betweenness"], expected_betweenness, atol=1e-6)

    # Eigenvector centrality for a star: hub > leaves, exact values depend on normalization.
    # Verify hub has the largest value and leaves are equal.
    hub_val = cent["eigenvector"][0]
    leaf_vals = cent["eigenvector"][1:]
    assert hub_val > leaf_vals.max()
    assert np.allclose(leaf_vals, leaf_vals[0], atol=1e-6)

# ----------------------------------------------------------------------
# Test PLI on perfectly phase‑locked signals (should be ~1.0)
# ----------------------------------------------------------------------
def test_compute_pli_perfect_phase_lock():
    sfreq = 100.0
    n_epochs = 3
    n_channels = 2
    t = np.arange(0, 2, 1 / sfreq)  # 2 s epoch
    # Two sine waves with a constant phase offset of π/2 (90°)
    sig1 = np.sin(2 * np.pi * 6 * t)  # 6 Hz within theta band
    sig2 = np.sin(2 * np.pi * 6 * t + np.pi / 2)

    epoch_data = np.stack(
        [np.stack([sig1, sig2]) for _ in range(n_epochs)], axis=0
    )  # shape (n_epochs, 2, n_times)

    pli_mat = compute_pli(epoch_data, sfreq=sfreq, band=(4, 8))
    # Off‑diagonal element should be close to 1.0 for perfect lag
    assert np.isclose(pli_mat[0, 1], 1.0, atol=1e-2)
    # Diagonal is defined as 1.0
    assert np.isclose(pli_mat[0, 0], 1.0)
    assert np.isclose(pli_mat[1, 1], 1.0)

# ----------------------------------------------------------------------
# Test VIF on correlated synthetic data (should exceed 5.0)
# ----------------------------------------------------------------------
def test_calculate_vif_correlated_features():
    rng = np.random.default_rng(1)
    size = 100
    x1 = rng.normal(size=size)
    x2 = x1 * 0.9 + rng.normal(scale=0.1, size=size)  # highly correlated with x1
    df = pd.DataFrame({"x1": x1, "x2": x2, "y": rng.normal(size=size)})

    vif = calculate_vif(df, features=["x1", "x2"])
    assert "x1" in vif and "x2" in vif
    # With such strong correlation VIF should be > 5
    assert vif["x1"] > 5.0
    assert vif["x2"] > 5.0

# ----------------------------------------------------------------------
# Test aggregation of subject metrics into the required CSV schema
# ----------------------------------------------------------------------
def test_aggregate_subject_metrics_writes_csv(tmp_path):
    subject_id = "sub-01"
    centrality = {
        "degree": np.array([0.5, 0.6]),
        "betweenness": np.array([0.2, 0.3]),
        "eigenvector": np.array([0.4, 0.5]),
    }
    pli = {"N1": 0.3, "N2": 0.35}
    vif = {"degree": 2.0, "betweenness": 3.0, "eigenvector": 1.5}
    out_csv = tmp_path / "SubjectMetrics.csv"

    aggregate_subject_metrics(
        subject_id=subject_id,
        centrality_dict=centrality,
        pli_dict=pli,
        vif_dict=vif,
        waking_night_id="night1",
        sleep_night_id="night2",
        temporal_proximity=False,
        output_path=str(out_csv),
    )

    # Verify file exists and contains required columns
    df = pd.read_csv(out_csv)
    required_cols = [
        "subject_id",
        "stage_label",
        "mean_pli",
        "n_epochs",
        "centrality_degree_mean",
        "centrality_betweenness_mean",
        "centrality_eigenvector_mean",
        "waking_night_id",
        "sleep_night_id",
        "temporal_proximity",
    ]
    for col in required_cols:
        assert col in df.columns

    # Verify values are as expected
    assert df.loc[0, "subject_id"] == subject_id
    assert np.isclose(df.loc[0, "mean_pli"], np.mean(list(pli.values())), atol=1e-8)
    assert np.isclose(df.loc[0, "centrality_degree_mean"], np.mean(centrality["degree"]), atol=1e-8)
    assert df.loc[0, "temporal_proximity"] is False

# ----------------------------------------------------------------------
# Ensure that compute_connectivity_matrix raises on invalid matrix
# ----------------------------------------------------------------------
def test_compute_connectivity_matrix_invalid_raises():
    raw = _make_fake_raw()
    # Monkey‑patch the internal function to return an invalid matrix
    def _bad_connectivity(*args, **kwargs):
        return np.array([[0, 2], [2, 0]])  # values > 1

    # Replace the private helper temporarily
    from metrics import compute_waking_connectivity

    original = compute_waking_connectivity
    try:
        # Inject bad function
        import types

        bad_func = types.FunctionType(_bad_connectivity.__code__, globals())
        globals()["compute_waking_connectivity"] = bad_func

        with pytest.raises(ValueError, match="failed validation"):
            compute_connectivity_matrix(raw, bands={"bad": (0, 1)})
    finally:
        # Restore original
        globals()["compute_waking_connectivity"] = original