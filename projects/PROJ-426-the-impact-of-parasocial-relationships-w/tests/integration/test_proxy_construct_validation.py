"""
Integration test for ``src.validation.validate_proxy_construct``.

The test creates a minimal, deterministic 30‑user dataset containing:
  * ``usage_frequency`` – integer counts drawn from a simple linear
    relationship with a synthetic PIS score.
  * ``pis_score`` – a continuous variable that is deliberately correlated
    with ``usage_frequency`` (r ≈ 0.8) so that the validation passes.

The test then invokes the validation script's ``main`` function and
checks that the generated YAML report exists and contains the expected
fields and a passing status.
"""

import os
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure the project root is on ``sys.path`` so that imports resolve.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from src.validation import validate_proxy_construct

def _create_test_artifacts(tmp_path: Path):
    """Write temporary usage‑metrics and PIS score parquet files."""
    # Deterministic random seed for reproducibility
    rng = np.random.default_rng(42)

    user_ids = [f"user_{i:03d}" for i in range(30)]

    # Generate a usage frequency (0‑20) and a PIS score that is
    # positively correlated (r ≈ 0.8).  We'll construct pis_score as
    # 0.5 * usage + noise.
    usage = rng.integers(0, 20, size=30)
    noise = rng.normal(loc=0.0, scale=2.0, size=30)
    pis = 0.5 * usage + noise

    usage_df = pd.DataFrame(
        {"user_id": user_ids, "usage_frequency": usage.astype(int)}
    )
    pis_df = pd.DataFrame({"user_id": user_ids, "pis_score": pis.astype(float)})

    # Write to the canonical locations expected by the validation script.
    usage_path = Path(tmp_path) / "data" / "processed"
    pis_path = Path(tmp_path) / "data" / "raw"
    usage_path.mkdir(parents=True, exist_ok=True)
    pis_path.mkdir(parents=True, exist_ok=True)

    usage_df.to_parquet(usage_path / "usage_metrics.parquet", index=False)
    pis_df.to_parquet(pis_path / "pis_scores.parquet", index=False)

    return usage_path / "usage_metrics.parquet", pis_path / "pis_scores.parquet"

def test_proxy_construct_validation_passes(tmp_path: Path):
    """
    The validation should succeed (r ≥ 0.6 and p < 0.05) and produce a
    YAML report with the correct structure.
    """
    # Arrange – create the artefacts in a temporary project‑root‑like layout
    usage_file, pis_file = _create_test_artifacts(tmp_path)

    # Monkey‑patch the path constants in the validation module so that it
    # reads from our temporary files instead of the real project directories.
    validate_proxy_construct.USAGE_METRICS_PATH = usage_file
    validate_proxy_construct.PIS_SCORES_PATH = pis_file
    validate_proxy_construct.REPORT_PATH = Path(tmp_path) / "data" / "validation" / "proxy_construct_report.yaml"

    # Act – run the validation script
    exit_code = validate_proxy_construct.main()
    assert exit_code == 0, "Validation script exited with an error"

    # Assert – the report exists and contains the expected keys
    assert validate_proxy_construct.REPORT_PATH.exists(), "Report file was not created"

    with open(validate_proxy_construct.REPORT_PATH, "r", encoding="utf-8") as f:
        report = yaml.safe_load(f)

    # Expected keys
    for key in ("r", "p_value", "pass"):
        assert key in report, f"Missing key '{key}' in report"

    # The synthetic data should give a strong positive correlation;
    # we therefore expect ``pass`` to be True.
    assert report["pass"] is True, "Correlation did not meet the required threshold"

    # Basic sanity checks on the numeric values
    assert isinstance(report["r"], float)
    assert isinstance(report["p_value"], float)
    assert -1.0 <= report["r"] <= 1.0
    assert 0.0 <= report["p_value"] <= 1.0