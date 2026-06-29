"""
Integration test for the training pipeline (US‑2).

The test creates a tiny synthetic dataset, invokes the pipeline and checks
that the contractual expectations are met:
  * Primary model converges in ≤ 100 iterations and has at least one
    non‑zero coefficient.
  * Alternative Random Forest achieves an ROC‑AUC within ±0.05 of the
    primary model.
  * The model artefacts are written to disk.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure the ``code`` directory is on the import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # repository root
CODE_ROOT = PROJECT_ROOT / "code"
sys.path.append(str(CODE_ROOT))

from modeling.pipeline import run_training_pipeline

@pytest.fixture
def synthetic_train_csv(tmp_path: Path) -> Path:
    """Create a small synthetic training CSV file."""
    rng = np.random.default_rng(0)
    n_samples = 200
    # Generate three correlated metrics
    metric1 = rng.normal(loc=50, scale=10, size=n_samples)
    metric2 = metric1 * 0.8 + rng.normal(scale=5, size=n_samples)  # correlated
    metric3 = rng.normal(loc=30, scale=7, size=n_samples)

    # Binary bug label with some signal
    logits = -3 + 0.04 * metric1 - 0.03 * metric2 + 0.02 * metric3
    prob = 1 / (1 + np.exp(-logits))
    bug_label = rng.binomial(1, prob)

    df = pd.DataFrame(
        {
            "metric1": metric1,
            "metric2": metric2,
            "metric3": metric3,
            "bug_label": bug_label,
        }
    )
    csv_path = tmp_path / "train.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_training_pipeline_end_to_end(synthetic_train_csv: Path, tmp_path: Path):
    """Run the pipeline and assert contractual guarantees."""
    model_dir = tmp_path / "models"

    # Execute the pipeline
    results = run_training_pipeline(str(synthetic_train_csv), str(model_dir))

    # Primary model convergence
    assert results["primary_iterations"] <= 100, "Primary model exceeded iteration limit"
    # At least one non‑zero coefficient – we read the saved model
    import joblib

    primary_model = joblib.load(Path(model_dir) / "primary.pkl")
    coeffs = np.asarray(primary_model.coef_).ravel()
    assert np.any(np.abs(coeffs) > 1e-6), "Primary model has all zero coefficients"

    # Alternative model ROC‑AUC tolerance
    auc_diff = results["auc_diff"]
    assert auc_diff <= 0.05, f"Alternative model AUC differs by {auc_diff:.3f} (> 0.05)"

    # Model artefacts exist
    assert (model_dir / "primary.pkl").exists(), "Primary model file missing"
    assert (model_dir / "alternative.pkl").exists(), "Alternative model file missing"

    # Spearman correlation sanity check (should be a real number)
    spearman = results["spearman_corr"]
    assert -1.0 <= spearman <= 1.0, "Spearman correlation out of bounds"
