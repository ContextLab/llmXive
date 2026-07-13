"""
Unit test for the ``code.analysis.correlations`` module.
It checks that the end‑to‑end ``main`` function creates the three expected CSV
artefacts when supplied with a minimal, real‑looking metrics file.
"""

import os
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test
from code.analysis import correlations

@pytest.fixture
def tiny_metrics_csv(tmp_path: Path) -> Path:
    """Create a tiny but realistic metrics CSV for the test."""
    df = pd.DataFrame(
        {
            "subject_id": [1, 2, 3],
            "modularity": [0.35, 0.40, 0.38],
            "global_efficiency": [0.55, 0.60, 0.58],
            "participation_coef": [0.22, 0.25, 0.23],
            "within_module_degree": [0.12, 0.15, 0.13],
        }
    )
    out_path = tmp_path / "metrics.csv"
    df.to_csv(out_path, index=False)
    return out_path

def test_end_to_end_creates_files(tmp_path: Path, monkeypatch, tiny_metrics_csv):
    """Run ``correlations.main`` with the tiny CSV and verify outputs."""
    # Patch the default path used inside the module to point at our temp file
    monkeypatch.setattr(correlations, "load_metrics_data", lambda: pd.read_csv(tiny_metrics_csv))

    # Run the analysis
    correlations.main()

    # Expected artefacts
    expected_files = [
        Path("data/analysis/pca_loadings.csv"),
        Path("data/analysis/factor_scores.csv"),
        Path("data/analysis/full_metrics.csv"),
        Path("data/analysis/correlation_matrix.csv"),
    ]

    for f in expected_files:
        assert f.is_file(), f"Expected output file {f} was not created"