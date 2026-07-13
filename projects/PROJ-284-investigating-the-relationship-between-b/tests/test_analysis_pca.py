"""
Unit test for the PCA analysis implemented in ``analysis/correlations.py``.
The test creates a tiny synthetic but *real* DataFrame that mimics the
structure of the metric CSV produced by earlier steps, runs the pipeline,
and checks that the three expected output files are created and contain
sensible data (non‑empty, correct columns).
"""

import os
import shutil
from pathlib import Path

import pandas as pd
import pytest

# Import the functions under test
from analysis import correlations as corr

ANALYSIS_DIR = Path("data/analysis")
METRICS_FILE = ANALYSIS_DIR / "metrics.csv"
LOADINGS_FILE = ANALYSIS_DIR / "pca_loadings.csv"
FACTOR_SCORES_FILE = ANALYSIS_DIR / "factor_scores.csv"
FULL_METRICS_FILE = ANALYSIS_DIR / "full_metrics.csv"

@pytest.fixture(scope="function")
def clean_analysis_dir(tmp_path):
    """
    Ensure a clean ``data/analysis`` directory for each test run.
    """
    # Move the repository's analysis dir to a temporary location
    if ANALYSIS_DIR.exists():
        backup = tmp_path / "backup"
        shutil.move(str(ANALYSIS_DIR), str(backup))
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Restore original content after the test
    if backup.exists():
        shutil.rmtree(str(ANALYSIS_DIR))
        shutil.move(str(backup), str(ANALYSIS_DIR))

def test_pca_pipeline_creates_outputs(clean_analysis_dir):
    # ------------------------------------------------------------------
    # 1. Create a minimal but realistic metrics CSV
    # ------------------------------------------------------------------
    df = pd.DataFrame(
        {
            "subject_id": [1, 2, 3, 4],
            "modularity": [0.4, 0.35, 0.42, 0.38],
            "global_efficiency": [0.55, 0.58, 0.53, 0.56],
            "participation_coef": [0.32, 0.30, 0.35, 0.31],
            "within_module_degree": [1.2, 1.1, 1.3, 1.15],
        }
    )
    df.to_csv(METRICS_FILE, index=False)

    # ------------------------------------------------------------------
    # 2. Run the full pipeline
    # ------------------------------------------------------------------
    corr.main()

    # ------------------------------------------------------------------
    # 3. Verify that the three output files exist
    # ------------------------------------------------------------------
    for path in (LOADINGS_FILE, FACTOR_SCORES_FILE, FULL_METRICS_FILE):
        assert path.is_file(), f"Expected output file {path} to exist"

    # ------------------------------------------------------------------
    # 4. Basic sanity checks on the contents
    # ------------------------------------------------------------------
    loadings = pd.read_csv(LOADINGS_FILE, index_col="metric")
    assert set(loadings.columns) == {"component_1", "component_2"}
    assert not loadings.empty

    scores = pd.read_csv(FACTOR_SCORES_FILE)
    assert list(scores.columns) == ["subject_id", "pca_factor_1"]
    assert len(scores) == len(df)

    full = pd.read_csv(FULL_METRICS_FILE)
    expected_cols = set(df.columns) | {"pca_factor_1"}
    assert set(full.columns) == expected_cols
    assert len(full) == len(df)