import json
import os
import tempfile
from pathlib import Path
import pytest

# Add parent to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.review_final_validation import (
    validate_fr001, validate_fr002, validate_fr003, 
    validate_fr004, validate_fr005, run_validation, generate_report
)

def test_validate_fr001_success():
    """Test FR-001 validation with valid seed count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a fake aggregated metrics file
        fake_agg = {"seed_count": 5, "metrics": {"mean_auc": 0.85}}
        agg_path = Path(tmpdir) / "frozen_baseline_aggregated_test.json"
        with open(agg_path, 'w') as f:
            json.dump(fake_agg, f)

        data = {"frozen_baseline_aggregated_path": str(agg_path)}
        result = validate_fr001(data)
        
        assert result["status"] == "passed"
        assert result["seed_count"] == 5

def test_validate_fr001_failure_low_seeds():
    """Test FR-001 validation with insufficient seeds."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_agg = {"seed_count": 1, "metrics": {"mean_auc": 0.85}}
        agg_path = Path(tmpdir) / "frozen_baseline_aggregated_test.json"
        with open(agg_path, 'w') as f:
            json.dump(fake_agg, f)

        data = {"frozen_baseline_aggregated_path": str(agg_path)}
        result = validate_fr001(data)
        
        assert result["status"] == "failed"
        assert "Seed count 1 < 2" in result["reason"]

def test_validate_fr002_success():
    """Test FR-002 validation with valid memory and time."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_runtime = {"peak_memory_gb": 6.5, "total_runtime_hours": 5.5}
        runtime_path = Path(tmpdir) / "runtime_report.json"
        with open(runtime_path, 'w') as f:
            json.dump(fake_runtime, f)

        data = {"runtime_report_path": str(runtime_path)}
        result = validate_fr002(data)
        
        assert result["status"] == "passed"

def test_validate_fr002_failure_memory():
    """Test FR-002 validation with high memory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_runtime = {"peak_memory_gb": 7.5, "total_runtime_hours": 5.5}
        runtime_path = Path(tmpdir) / "runtime_report.json"
        with open(runtime_path, 'w') as f:
            json.dump(fake_runtime, f)

        data = {"runtime_report_path": str(runtime_path)}
        result = validate_fr002(data)
        
        assert result["status"] == "failed"
        assert "exceeds 7GB" in result["reason"]

def test_validate_fr003_success():
    """Test FR-003 validation with valid correlation report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Integrity report
        integrity = {"skipped_datasets": ["dataset_zero_var"]}
        integrity_path = Path(tmpdir) / "data_integrity_report.json"
        with open(integrity_path, 'w') as f:
            json.dump(integrity, f)

        # Correlation report
        corr = {"correlations": {"cardinality": 0.5}, "fdr_adjusted": {"cardinality": 0.03}}
        corr_path = Path(tmpdir) / "correlation_report_test.json"
        with open(corr_path, 'w') as f:
            json.dump(corr, f)

        data = {
            "data_integrity_report_path": str(integrity_path),
            "correlation_report_path": str(corr_path)
        }
        result = validate_fr003(data)
        
        assert result["status"] == "passed"
        assert result["skipped_datasets_count"] == 1

def test_validate_fr004_failure_time():
    """Test FR-004 validation with high runtime."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_runtime = {"peak_memory_gb": 6.0, "total_runtime_hours": 6.5}
        runtime_path = Path(tmpdir) / "runtime_report.json"
        with open(runtime_path, 'w') as f:
            json.dump(fake_runtime, f)

        data = {"runtime_report_path": str(runtime_path)}
        result = validate_fr004(data)
        
        assert result["status"] == "failed"
        assert "Time constraint violated" in result["reason"]

def test_validate_fr005_success():
    """Test FR-005 validation with valid baselines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Baselines
        baselines = [{"dataset_id": "d1", "auc": 0.9}]
        baselines_path = Path(tmpdir) / "gpu_tuned_baselines.csv" # Using JSON for simplicity in test, logic checks content
        with open(baselines_path, 'w') as f:
            json.dump(baselines, f)

        # Frozen metrics
        frozen = {"dataset_id": "d1", "auc": 0.8}
        frozen_path = Path(tmpdir) / "frozen_baseline_metrics_test.json"
        with open(frozen_path, 'w') as f:
            json.dump(frozen, f)

        data = {
            "gpu_baselines_path": str(baselines_path),
            "frozen_baseline_metrics_path": str(frozen_path)
        }
        result = validate_fr005(data)
        
        assert result["status"] == "passed"

def test_generate_report_creates_file():
    """Test that generate_report creates a valid markdown file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        validation_results = {
            "timestamp": "2023-01-01T00:00:00",
            "overall_status": "passed",
            "fr_requirements": {
                "FR-001": {"status": "passed"},
                "FR-002": {"status": "passed"},
                "FR-003": {"status": "passed"},
                "FR-004": {"status": "passed"},
                "FR-005": {"status": "passed"}
            }
        }
        
        output_path = Path(tmpdir) / "report.md"
        generate_report(validation_results, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Final Validation Report" in content
        assert "FR-001" in content
        assert "FR-005" in content
        assert "PASSED" in content
