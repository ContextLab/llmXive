"""Integration test ensuring the end‑to‑end training pipeline works."""

import json
from pathlib import Path

import pytest

from code import _04_train_model as train_mod

@pytest.fixture
def minimal_dataset(tmp_path):
    """Create minimal but realistic CSV files for the pipeline."""
    # Graph metrics (10 subjects, 5 features)
    graph_df = Path(tmp_path, "data", "processed", "graph_metrics.csv")
    graph_df.parent.mkdir(parents=True, exist_ok=True)
    graph_df.write_text(
        "subject_id,metric_1,metric_2,metric_3,metric_4,metric_5\\n"
        "sub-001,0.1,0.2,0.3,0.4,0.5\\n"
        "sub-002,0.2,0.1,0.4,0.3,0.6\\n"
        "sub-003,0.3,0.2,0.1,0.5,0.4\\n"
        "sub-004,0.4,0.3,0.2,0.1,0.7\\n"
        "sub-005,0.5,0.4,0.3,0.2,0.8\\n"
        "sub-006,0.6,0.5,0.4,0.3,0.9\\n"
        "sub-007,0.7,0.6,0.5,0.4,1.0\\n"
        "sub-008,0.8,0.7,0.6,0.5,1.1\\n"
        "sub-009,0.9,0.8,0.7,0.6,1.2\\n"
        "sub-010,1.0,0.9,0.8,0.7,1.3\\n"
    )

    # Eligible subjects with MMSE scores
    eligible_df = Path(tmp_path, "data", "processed", "eligible_subjects.csv")
    eligible_df.write_text(
        "subject_id,mmse_baseline,mmse_followup\\n"
        "sub-001,30,27\\n"
        "sub-002,29,28\\n"
        "sub-003,28,25\\n"
        "sub-004,27,27\\n"
        "sub-005,30,26\\n"
        "sub-006,29,29\\n"
        "sub-007,28,24\\n"
        "sub-008,27,27\\n"
        "sub-009,30,29\\n"
        "sub-010,29,28\\n"
    )

    return tmp_path

def test_end_to_end_training(monkeypatch, minimal_dataset):
    """Run the full training script against the minimal dataset."""
    # Redirect the Path used in the module to the temporary location
    monkeypatch.setattr(train_mod, "Path", lambda *p: minimal_dataset / Path(*p))

    # Execute main; expect a clean exit
    assert train_mod.main() == 0

    # Check artefacts
    model_file = minimal_dataset / "data" / "processed" / "model.pkl"
    report_file = minimal_dataset / "data" / "processed" / "performance_report.json"
    assert model_file.is_file()
    assert report_file.is_file()

    # Validate JSON structure
    with report_file.open() as f:
        data = json.load(f)
    assert "mean_roc_auc" in data
    assert "best_params" in data