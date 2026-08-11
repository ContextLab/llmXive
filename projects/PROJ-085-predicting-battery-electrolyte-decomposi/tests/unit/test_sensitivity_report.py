import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.sensitivity_report_generator import (
    load_sensitivity_results,
    load_model_info,
    generate_report_content,
    run_report_generation
)
from config import get_config

@pytest.fixture
def mock_model_run_data():
    """Fixture to provide mock model run data for testing."""
    return {
        "model_type": "RandomForestRegressor",
        "r2_score": 0.85,
        "mae": 0.12,
        "deviation_note": "Internal DFT validation used as fallback.",
        "sensitivity_analysis": {
            "thresholds": [0.45, 0.50, 0.55],
            "rank_stability": {
                "0.45": "Stable",
                "0.50": "Stable",
                "0.55": "Stable"
            },
            "feature_ranks": {
                "0.45": ["homo_energy", "lumo_energy", "bond_length_avg"],
                "0.50": ["homo_energy", "lumo_energy", "bond_length_avg"],
                "0.55": ["homo_energy", "lumo_energy", "bond_length_avg"]
            }
        }
    }

def test_generate_report_content(mock_model_run_data):
    """Test that report content is generated correctly."""
    sensitivity_results = mock_model_run_data["sensitivity_analysis"]
    model_info = {
        "model_type": mock_model_run_data["model_type"],
        "r2_score": mock_model_run_data["r2_score"],
        "mae": mock_model_run_data["mae"],
        "deviation_note": mock_model_run_data["deviation_note"]
    }

    content = generate_report_content(sensitivity_results, model_info)

    # Check for key sections
    assert "Sensitivity Analysis Report" in content
    assert "Executive Summary" in content
    assert "Model Performance Metrics" in content
    assert "Sensitivity Sweep Configuration" in content
    assert "Rank Stability Analysis" in content
    assert "Conclusion" in content

    # Check for specific values
    assert "0.45" in content
    assert "0.50" in content
    assert "0.55" in content
    assert "homo_energy" in content
    assert "lumo_energy" in content
    assert "0.85" in content
    assert "0.12" in content

    # Check deviation note
    assert "Internal DFT validation used as fallback" in content

def test_run_report_generation(mock_model_run_data):
    """Test the full report generation pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup mock config
        config_path = os.path.join(tmpdir, "config.json")
        with open(config_path, 'w') as f:
            json.dump({
                "model_run_path": os.path.join(tmpdir, "model_run.json"),
                "validation_dir": tmpdir
            }, f)

        # Write mock model run data
        model_run_path = os.path.join(tmpdir, "model_run.json")
        with open(model_run_path, 'w') as f:
            json.dump(mock_model_run_data, f)

        # Patch get_config to return our temp config
        with patch('models.sensitivity_report_generator.get_config', return_value={
            "model_run_path": model_run_path,
            "validation_dir": tmpdir
        }):
            output_path = run_report_generation()

            # Verify file exists
            assert os.path.exists(output_path)
            assert output_path.endswith("sensitivity_report.md")

            # Verify content
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "Sensitivity Analysis Report" in content
            assert "homo_energy" in content

def test_load_sensitivity_results_missing_file():
    """Test that appropriate error is raised if model run file is missing."""
    with patch('models.sensitivity_report_generator.get_config', return_value={
        "model_run_path": "/nonexistent/path/model_run.json"
    }):
        with pytest.raises(FileNotFoundError, match="Sensitivity results not found"):
            load_sensitivity_results()

def test_load_sensitivity_results_missing_key():
    """Test that appropriate error is raised if sensitivity key is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_run_path = os.path.join(tmpdir, "model_run.json")
        with open(model_run_path, 'w') as f:
            json.dump({"some_other_key": {}})
        
        with patch('models.sensitivity_report_generator.get_config', return_value={
            "model_run_path": model_run_path
        }):
            with pytest.raises(ValueError, match="Sensitivity analysis data not found"):
                load_sensitivity_results()
