import json
import tempfile
from pathlib import Path
import pytest

from ingest.bias_check import (
    ExclusionReason,
    BiasReport,
    load_exclusion_log,
    analyze_exclusion_bias,
    write_bias_report
)
from utils.config import Config

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_exclusion_logs():
    return [
        {"reason": "incomplete_tensor", "family_id": "TMD_1"},
        {"reason": "incomplete_tensor", "family_id": "TMD_1"},
        {"reason": "non_2d", "family_id": "TMD_2"},
        {"reason": "incomplete_tensor", "family_id": "TMD_3"},
        {"reason": "high_energy", "family_id": "TMD_1"},
    ]

def test_load_exclusion_log_missing_file(temp_dir):
    path = temp_dir / "missing.json"
    logs = load_exclusion_log(path)
    assert logs == []

def test_load_exclusion_log_valid(temp_dir, sample_exclusion_logs):
    path = temp_dir / "valid.json"
    with open(path, 'w') as f:
        json.dump(sample_exclusion_logs, f)
    
    logs = load_exclusion_log(path)
    assert len(logs) == 5
    assert logs[0]["reason"] == "incomplete_tensor"

def test_analyze_exclusion_bias(sample_exclusion_logs):
    config = Config()
    report = analyze_exclusion_bias(sample_exclusion_logs, config)
    
    assert report.total_excluded == 5
    assert len(report.exclusions) == 3  # 3 unique reasons
    
    # Check counts
    reason_counts = {r.reason: r.count for r in report.exclusions}
    assert reason_counts["incomplete_tensor"] == 3
    assert reason_counts["non_2d"] == 1
    assert reason_counts["high_energy"] == 1
    
    # Check flagged families (threshold is count >= 2)
    # TMD_1 has 3 exclusions, so it should be flagged.
    assert "TMD_1" in report.flagged_families
    assert "TMD_2" not in report.flagged_families
    assert "TMD_3" not in report.flagged_families

def test_write_bias_report(temp_dir, sample_exclusion_logs):
    config = Config()
    report = analyze_exclusion_bias(sample_exclusion_logs, config)
    
    output_path = temp_dir / "report.json"
    write_bias_report(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["total_excluded"] == 5
    assert "TMD_1" in saved_report["flagged_families"]
    assert "Potential bias detected" in saved_report["summary"]

def test_empty_logs(temp_dir):
    logs = []
    config = Config()
    report = analyze_exclusion_bias(logs, config)
    
    assert report.total_excluded == 0
    assert report.exclusions == []
    assert report.flagged_families == []
    assert "No exclusion logs" in report.summary or "0" in report.summary
