"""
Unit tests for T016b: generate_validation_report.py
"""
import os
import sys
import json
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil

# Ensure code/ is in path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from ingestion.generate_validation_report import (
    load_ingestion_status,
    load_validation_metrics,
    generate_validation_report,
    save_report
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_load_ingestion_status_success(temp_dir):
    """Test loading a valid status JSON file."""
    status_file = temp_dir / "status.json"
    data = {"threshold_status": "N>=100", "exact_N": 120}
    with open(status_file, 'w') as f:
        json.dump(data, f)
    
    result = load_ingestion_status(status_file)
    assert result["threshold_status"] == "N>=100"
    assert result["exact_N"] == 120

def test_load_ingestion_status_missing(temp_dir):
    """Test loading a missing status file raises error."""
    status_file = temp_dir / "missing.json"
    with pytest.raises(FileNotFoundError):
        load_ingestion_status(status_file)

def test_load_validation_metrics_success(temp_dir):
    """Test loading a valid metrics YAML file."""
    metrics_file = temp_dir / "metrics.yaml"
    data = {"pass_rate_percentage": 95.5}
    with open(metrics_file, 'w') as f:
        yaml.dump(data, f)
    
    result = load_validation_metrics(metrics_file)
    assert result["pass_rate_percentage"] == 95.5

def test_generate_validation_report_complete():
    """Test report generation with all fields."""
    status = {
        "threshold_status": "50<=N<100",
        "exact_N": 80,
        "excluded_count": 5,
        "power_limitation_warning": "N < 100"
    }
    metrics = {
        "total_raw_records": 85,
        "passed_threshold_count": 80,
        "failed_threshold_count": 5,
        "pass_rate_percentage": 94.1
    }
    
    report = generate_validation_report(status, metrics)
    
    assert report["status"] == "50<=N<100"
    assert report["count"] == 80
    assert report["excluded_count"] == 5
    assert report["pass_rate_percentage"] == 94.1
    assert report["total_raw_records"] == 85
    assert report["power_limitation_warning"] == "N < 100"

def test_generate_validation_report_minimal():
    """Test report generation with minimal fields."""
    status = {
        "threshold_status": "N<50",
        "exact_N": 40
    }
    metrics = {
        "total_raw_records": 45,
        "passed_threshold_count": 40,
        "failed_threshold_count": 5,
        "pass_rate_percentage": 88.8
    }
    
    report = generate_validation_report(status, metrics)
    
    assert report["status"] == "N<50"
    assert report["count"] == 40
    assert report["excluded_count"] == 0 # Default
    assert "power_limitation_warning" not in report # Not in status