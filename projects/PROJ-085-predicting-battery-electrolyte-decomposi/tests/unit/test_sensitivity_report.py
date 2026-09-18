import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Mock the config and logging to avoid dependency on full project setup during unit tests
# In a real integration test, these would use the actual config
import sys
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.sensitivity_report_generator import (
    load_sensitivity_results,
    load_model_info,
    generate_report_content,
    run_report_generation
)

@pytest.fixture
def mock_sensitivity_data():
    return {
        "thresholds_swept": [0.45, 0.50, 0.55],
        "rank_stability": {
            "max_rank_shift": 0,
            "is_stable": True
        },
        "feature_shifts": {
            "0.45": {"top_3": ["homo", "lumo", "bond_length_c1"]},
            "0.50": {"top_3": ["homo", "lumo", "bond_length_c1"]},
            "0.55": {"top_3": ["homo", "lumo", "bond_length_c1"]},
            "shifted_high_potential": ["bond_angle_o1_c1"]
        },
        "internal_metrics": {
            "mae": 0.12,
            "r2": 0.85
        }
    }

@pytest.fixture
def mock_model_data():
    return {
        "r2_score": 0.85,
        "mae": 0.12,
        "model_type": "RandomForest"
    }

def test_generate_report_content(mock_sensitivity_data, mock_model_data):
    """Test that the report content is generated correctly with expected sections."""
    content = generate_report_content(mock_sensitivity_data, mock_model_data)
    
    # Check for required sections
    assert "Executive Summary" in content
    assert "Methodology" in content
    assert "Rank Stability Analysis" in content
    assert "Feature Importance Shifts" in content
    assert "Warnings and Deviations" in content
    
    # Check for specific data points
    assert "0.45" in content
    assert "0.50" in content
    assert "0.55" in content
    assert "homo" in content
    assert "bond_angle_o1_c1" in content
    
    # Check for warning text
    assert "FR-006 and SC-003" in content
    assert "External Validation" in content
    assert "Internal DFT validation" in content

@patch('models.sensitivity_report_generator.get_validation_dir')
@patch('models.sensitivity_report_generator.load_sensitivity_results')
@patch('models.sensitivity_report_generator.load_model_info')
def test_run_report_generation_success(
    mock_load_model, 
    mock_load_sens, 
    mock_get_validation, 
    mock_sensitivity_data, 
    mock_model_data,
    tmp_path
):
    """Test the full pipeline writes the file correctly."""
    # Setup mocks
    mock_load_sens.return_value = mock_sensitivity_data
    mock_load_model.return_value = mock_model_data
    
    # Mock the output directory
    mock_get_validation_dir.return_value = tmp_path
    
    # Run
    success = run_report_generation()
    
    assert success is True
    assert (tmp_path / "sensitivity_report.md").exists()
    
    # Verify content
    with open(tmp_path / "sensitivity_report.md", 'r') as f:
        content = f.read()
    assert "Executive Summary" in content

@patch('models.sensitivity_report_generator.load_sensitivity_results')
def test_run_report_generation_fail_missing_sens(mock_load_sens):
    """Test failure when sensitivity results are missing."""
    mock_load_sens.return_value = None
    success = run_report_generation()
    assert success is False

@patch('models.sensitivity_report_generator.load_sensitivity_results')
@patch('models.sensitivity_report_generator.load_model_info')
def test_run_report_generation_fail_missing_model(mock_load_sens, mock_load_model, mock_sensitivity_data):
    """Test failure when model info is missing."""
    mock_load_sens.return_value = mock_sensitivity_data
    mock_load_model.return_value = None
    success = run_report_generation()
    assert success is False
