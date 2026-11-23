import os
import json
import pytest
from pathlib import Path

def test_quickstart_report_exists():
    """Verify that the quickstart validation produced a report."""
    report_path = Path('data/logs/quickstart_validation_report.json')
    assert report_path.exists(), "Quickstart validation report missing"

def test_quickstart_report_status():
    """Verify the validation status in the report."""
    report_path = Path('data/logs/quickstart_validation_report.json')
    if not report_path.exists():
        pytest.skip("Report not generated yet")
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['status'] == 'success', f"Validation failed: {report}"

def test_required_outputs_exist():
    """Verify key output files from the quickstart flow exist."""
    required_files = [
        'data/processed/raw_extract.parquet',
        'data/processed/filtered.parquet',
        'data/processed/sampled_dataset.parquet',
        'data/models/estimator_checkpoint_final.pt',
        'data/processed/hybrid_output.parquet',
        'data/logs/threshold_validation.log',
        'data/metrics/power_analysis_final.json'
    ]
    
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        pytest.fail(f"Missing required output files: {missing}")
