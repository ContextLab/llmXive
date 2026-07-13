"""
Unit test for the PCA implementation in ``code.analysis.correlations``.
The test uses a tiny synthetic dataset (generated on the fly) to verify
that the three required output files are created and contain sensible
values.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from code.analysis.correlations import (
    load_metrics_data,
    compute_and_save_pca,
    load_pca_scores,
    merge_metrics_and_pca_scores,
    save_full_metrics,
)

# Directory where the analysis artefacts are written.
ANALYSIS_DIR = Path("data/analysis")
METRICS_CSV = ANALYSIS_DIR / "metrics.csv"

@pytest.fixture(scope="function")
def synthetic_metrics(tmp_path):
    """Create a small synthetic metrics CSV for the duration of a test."""
    df = pd.DataFrame(
        {
            "subject_id": [1, 2, 3, 4],
            "modularity": [0.2, 0.25, 0.22, 0.24],
            "global_efficiency": [0.45, 0.48, 0.46, 0.47],
            "participation_coef": [0.33, 0.35, 0.34, 0.36],
            "within_module_degree": [0.55, 0.58, 0.57, 0.56],
        }
    )
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(METRICS_CSV, index=False)
    yield df
    # Cleanup after test
    for f in ANALYSIS_DIR.iterdir():
        f.unlink()
    ANALYSIS_DIR.rmdir()

def test_pca_workflow(synthetic_metrics):
    # Load the synthetic data
    df = load_metrics_data()
    assert not df.empty
    # Run PCA
    compute_and_save_pca(df, n_components=2)

    # Verify that the expected files exist
    loadings_path = ANALYSIS_DIR / "pca_loadings.csv"
    scores_path = ANALYSIS_DIR / "factor_scores.csv"
    full_metrics_path = ANALYSIS_DIR / "full_metrics.csv"

    for path in (loadings_path, scores_path, full_metrics_path):
        assert path.is_file(), f"{path} was not created"

    # Load back the artefacts and perform basic sanity checks
    loadings = pd.read_csv(loadings_path, index_col=0)
    scores = pd.read_csv(scores_path)
    full = pd.read_csv(full_metrics_path)

    # Loadings should have two component columns
    assert list(loadings.columns) == ["component_1", "component_2"]
    # Scores should have exactly one PCA factor column
    assert list(scores.columns) == ["subject_id", "pca_factor_1"]
    # Full metrics should contain the original columns plus the factor
    expected_cols = set(
        [
            "subject_id",
            "modularity",
            "global_efficiency",
            "participation_coef",
            "within_module_degree",
            "pca_factor_1",
        ]
    )
    assert set(full.columns) == expected_cols
    # Ensure the number of rows matches the input
    assert len(full) == len(df)

# The test suite can be executed via ``pytest -q`` from the repository root.