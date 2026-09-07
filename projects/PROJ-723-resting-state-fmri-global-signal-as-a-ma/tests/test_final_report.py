import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from run_final_report import aggregate_results, load_model_report, load_robustness_report, load_diagnostics, load_delta_r2

@pytest.fixture
def mock_input_files(tmp_path):
    """Create mock input files for testing."""
    results_dir = tmp_path / "data" / "results"
    results_dir.mkdir(parents=True)

    # Mock model_report.json
    model_data = {
        "observed_mae": 12.5,
        "observed_r": 0.35,
        "observed_r_squared": 0.12,
        "empirical_p_value": 0.02,
        "null_distribution": {
            "mean": 0.01,
            "std": 0.05,
            "count": 1000
        }
    }
    with open(results_dir / "model_report.json", "w") as f:
        json.dump(model_data, f)

    # Mock robustness_report.json
    robust_data = {
        "alpha_sweep": {
            "stable": True,
            "mae_range": [12.4, 12.6]
        },
        "variance_metric_analysis": {
            "pearson_r": 0.34,
            "significant": True
        },
        "partial_correlation": {
            "significant": True,
            "r": 0.30,
            "p_value": 0.01
        }
    }
    with open(results_dir / "robustness_report.json", "w") as f:
        json.dump(robust_data, f)

    # Mock diagnostics.json
    diag_data = {
        "vif_values": {
            "Global_Signal_SD": 1.2,
            "FD": 1.5,
            "DVARS": 1.3,
            "Age": 1.1,
            "Sex": 1.0
        }
    }
    with open(results_dir / "diagnostics.json", "w") as f:
        json.dump(diag_data, f)

    # Mock delta_r2.json
    delta_data = {
        "delta_r2": 0.08,
        "full_r2": 0.12,
        "reduced_r2": 0.04
    }
    with open(results_dir / "delta_r2.json", "w") as f:
        json.dump(delta_data, f)

    return tmp_path

def test_load_model_report(mock_input_files):
    with patch("run_final_report.project_root", mock_input_files):
        result = load_model_report()
        assert result["observed_mae"] == 12.5
        assert result["empirical_p_value"] == 0.02

def test_load_robustness_report(mock_input_files):
    with patch("run_final_report.project_root", mock_input_files):
        result = load_robustness_report()
        assert result["alpha_sweep"]["stable"] is True

def test_load_diagnostics(mock_input_files):
    with patch("run_final_report.project_root", mock_input_files):
        result = load_diagnostics()
        assert "Global_Signal_SD" in result["vif_values"]

def test_load_delta_r2(mock_input_files):
    with patch("run_final_report.project_root", mock_input_files):
        result = load_delta_r2()
        assert result["delta_r2"] == 0.08

def test_aggregate_results_structure(mock_input_files):
    with patch("run_final_report.project_root", mock_input_files):
        with patch("run_final_report.output_path", mock_input_files / "data" / "results" / "final_report.json"):
            report = aggregate_results()
            
            # Verify structure
            assert "components" in report
            assert "primary_model" in report["components"]
            assert "robustness_analysis" in report["components"]
            assert "collinearity_diagnostics" in report["components"]
            assert "reduced_model_comparison" in report["components"]
            
            # Verify summary
            assert "summary" in report
            assert report["summary"]["key_findings"]["observed_mae"] == 12.5
            assert report["summary"]["key_findings"]["delta_r2"] == 0.08
            assert report["summary"]["robustness_check"]["alpha_sweep_stable"] is True

def test_aggregate_results_file_creation(mock_input_files):
    output_file = mock_input_files / "data" / "results" / "final_report.json"
    
    with patch("run_final_report.project_root", mock_input_files):
        with patch("run_final_report.output_path", output_file):
            aggregate_results()
            
            assert output_file.exists()
            with open(output_file) as f:
                loaded = json.load(f)
                assert loaded["status"] == "complete"
                assert "project" in loaded
