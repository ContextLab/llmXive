"""
Unit tests for the validation report generator (Task T034).
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock config to avoid needing full project setup for tests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validation.report_generator import generate_validation_report, save_report

@pytest.fixture
def mock_files(tmp_path):
    """Create temporary mock data files."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    
    # Mock metrics.json
    metrics_data = {
        "random_forest": {"r2": 0.85, "rmse": 0.12, "mae": 0.09},
        "gradient_boosting": {"r2": 0.87, "rmse": 0.11, "mae": 0.08}
    }
    with open(models_dir / "metrics.json", 'w') as f:
        json.dump(metrics_data, f)
    
    # Mock linear_coef.json
    coef_data = {
        "size_mismatch_coefficient": -0.45,
        "p_value": 0.003
    }
    with open(models_dir / "linear_coef.json", 'w') as f:
        json.dump(coef_data, f)
    
    # Mock validation_stats.json
    stats_data = {
        "bootstrap_ci": {"lower": -0.60, "upper": -0.30},
        "stability": {
            "threshold_sweep_range": [0.45, 0.55],
            "variation": 0.02,
            "mean_rate": 0.80,
            "verification_status": "PASSED",
            "details": "Variation 0.02 is within ±5% of mean 0.80."
        }
    }
    with open(models_dir / "validation_stats.json", 'w') as f:
        json.dump(stats_data, f)
    
    return models_dir

def test_generate_validation_report_complete(mock_files, tmp_path):
    """Test report generation with all required files present."""
    # Patch the paths to use our temp directory
    with patch('code.validation.report_generator.MODELS_DIR', mock_files), \
         patch('code.validation.report_generator.REPORTS_DIR', tmp_path):
        
        report = generate_validation_report()
        
        assert report["status"] == "success"
        assert "random_forest" in report["metrics"]
        assert report["statistical_inference"]["p_value"] == 0.003
        assert report["statistical_inference"]["interpretation"] == "Significant"
        assert report["stability_analysis"]["verification_status"] == "PASSED"

def test_generate_validation_report_missing_metrics(mock_files, tmp_path):
    """Test report generation when metrics file is missing."""
    # Remove metrics file
    (mock_files / "metrics.json").unlink()
    
    with patch('code.validation.report_generator.MODELS_DIR', mock_files), \
         patch('code.validation.report_generator.REPORTS_DIR', tmp_path):
        
        report = generate_validation_report()
        
        assert report["status"] == "warning"
        assert "error" in report["metrics"]

def test_save_report(tmp_path):
    """Test saving the report to a file."""
    report = {
        "status": "success",
        "metrics": {"test": 1},
        "statistical_inference": {},
        "stability_analysis": {}
    }
    
    output_path = tmp_path / "test_report.json"
    saved_path = save_report(report, output_path)
    
    assert saved_path.exists()
    with open(saved_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == report
