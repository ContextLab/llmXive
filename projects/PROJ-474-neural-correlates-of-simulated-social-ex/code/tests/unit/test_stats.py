import json
from pathlib import Path

import pandas as pd
import pytest

from src.stats import generate_sensitivity_curve

@pytest.fixture
def dummy_qc_list(tmp_path, monkeypatch):
    """
    Create a minimal ``subject_qc_list.json`` with a few subjects and
    motion metrics that satisfy the thresholds.
    """
    data = [
        {"subject_id": "sub-01", "motion_metric": 2.9, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-02", "motion_metric": 3.1, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-03", "motion_metric": 3.5, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-04", "motion_metric": 4.2, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-05", "motion_metric": 2.5, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-06", "motion_metric": 3.7, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-07", "motion_metric": 3.0, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-08", "motion_metric": 3.3, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-09", "motion_metric": 3.9, "condition_status": "valid", "retained": True},
        {"subject_id": "sub-10", "motion_metric": 2.8, "condition_status": "valid", "retained": True},
    ]
    qc_path = Path("data/processed/subject_qc_list.json")
    qc_path.parent.mkdir(parents=True, exist_ok=True)
    with qc_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)
    return qc_path

@pytest.fixture
def dummy_connectivity_metrics(tmp_path, monkeypatch):
    """
    Minimal ``connectivity_metrics.json`` required for the sensitivity
    analysis.  The values are arbitrary but realistic.
    """
    metrics = {
        f"sub-{i:02d}": {"inclusion": 0.1 + i * 0.01, "exclusion": 0.15 + i * 0.01}
        for i in range(1, 11)
    }
    metrics_path = Path("data/processed/connectivity_metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f)
    return metrics_path

def test_generate_sensitivity_curve_creates_outputs(dummy_qc_list, dummy_connectivity_metrics):
    """
    After running the analysis we expect both the CSV and PNG to exist.
    """
    generate_sensitivity_curve()
    csv_path = Path("data/results/sensitivity_curve.csv")
    png_path = Path("data/results/sensitivity_curve.png")
    assert csv_path.is_file()
    assert png_path.is_file()
    # Basic sanity check on the CSV contents
    df = pd.read_csv(csv_path)
    assert "threshold" in df.columns
    assert "p_value" in df.columns
    assert len(df) == 6  # one row per threshold