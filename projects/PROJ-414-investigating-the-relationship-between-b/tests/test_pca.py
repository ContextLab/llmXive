"""Tests for T005 – PCA dimensionality reduction."""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA

from llmxive_toolkit import paths

# Ensure the code directory is on the import path.
CODE_DIR = paths.root / "code"
sys.path.insert(0, str(CODE_DIR))

import dimensionality  # noqa: E402
import config  # noqa: E402

def _load_metrics():
    """Load all metric files and return the concatenated descriptor matrix."""
    derived_dir = paths.data("derived")
    metric_files = sorted(derived_dir.glob("metrics_*.csv"))
    if not metric_files:
        pytest.skip("No metric files available – run the metrics stage first")
    rows = []
    for mf in metric_files:
        df = pd.read_csv(mf)
        # Assume descriptor columns are everything except subject_id and window_index
        descriptor_cols = [c for c in df.columns if c not in {"subject_id", "window_index"}]
        rows.append(df[descriptor_cols])
    return pd.concat(rows, ignore_index=True)

def test_pca_variance_threshold():
    """The retained components must explain at least the configured variance."""
    # Run the PCA stage to generate the output file.
    dimensionality.main([])

    pca_path = paths.data("derived", "pca_scores.csv")
    assert pca_path.is_file(), "PCA output file not created"

    df = pd.read_csv(pca_path)
    # All rows should have the same number of retained components.
    n_retained = df["n_components_retained"].iloc[0]
    assert n_retained >= 1

    # Verify the cumulative variance meets the threshold.
    variance_total = df["variance_explained_total"].iloc[0]
    assert (
        variance_total >= config.PCA_VARIANCE_THRESHOLD - 1e-6
    ), f"Cumulative variance {variance_total:.3f} < required {config.PCA_VARIANCE_THRESHOLD}"

def test_pca_schema_compliance():
    """Each row must conform to the pca_scores.schema.yaml contract."""
    pca_path = paths.data("derived", "pca_scores.csv")
    if not pca_path.is_file():
        pytest.skip("PCA output not present")
    df = pd.read_csv(pca_path)

    required_cols = {"subject_id", "n_components_retained", "variance_explained_total", "pc_scores"}
    assert required_cols.issubset(set(df.columns)), "Missing required columns"

    for _, row in df.iterrows():
        # n_components_retained must be integer ≥ 1
        n = int(row["n_components_retained"])
        assert n >= 1

        # variance_explained_total must be between 0 and 1
        var = float(row["variance_explained_total"])
        assert 0.0 <= var <= 1.0

        # pc_scores must be a JSON object with exactly n entries
        pc_map = json.loads(row["pc_scores"])
        assert isinstance(pc_map, dict)
        assert len(pc_map) == n
        for key, val in pc_map.items():
            assert key.startswith("pc_")
            assert isinstance(val, float)

def test_pca_components_orthogonal():
    """Re‑fit PCA on the raw descriptor matrix and check orthogonality of components."""
    # Load raw descriptor matrix used by the pipeline.
    metric_df = _load_metrics()
    if metric_df.empty:
        pytest.skip("No metric data to test orthogonality")
    X = metric_df.to_numpy(dtype=np.float64)

    pca = PCA()
    pca.fit(X)
    components = pca.components_  # shape (n_components, n_features)

    # Orthogonality: dot product between distinct components should be ~0.
    dot_matrix = components @ components.T
    # Zero out the diagonal.
    np.fill_diagonal(dot_matrix, 0.0)
    max_off_diag = np.abs(dot_matrix).max()
    assert max_off_diag < 1e-10, f"Components not orthogonal (max off‑diag {max_off_diag})"