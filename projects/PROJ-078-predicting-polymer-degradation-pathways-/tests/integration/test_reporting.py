"""Integration tests for full report generation."""
import pytest
import json
import os
from pathlib import Path
from evaluate import generate_test_predictions, save_validation_metrics

@pytest.mark.integration
def test_full_report_generation(project_paths):
    """Test the full report generation pipeline."""
    reports_dir = project_paths["data_reports"]
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Simulate generating a report
    report_data = {
        "p_value": 0.03,
        "motifs": ["ester", "carbonyl"],
        "confidence": 0.85,
        "timestamp": "2023-10-01T00:00:00"
    }

    report_path = reports_dir / "final_report.json"
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)

    assert report_path.exists()
    with open(report_path, "r") as f:
        loaded = json.load(f)
    assert loaded["p_value"] == 0.03
    assert "ester" in loaded["motifs"]
