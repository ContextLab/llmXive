import pytest
import json
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import set_synthetic_mode, is_synthetic, initialize_methodology_validation_mode, is_methodology_validation_mode
from statistical_model import run_statistical_analysis

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a mock data directory with minimal data."""
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    results_dir = data_dir / "results"
    
    processed_dir.mkdir(parents=True)
    results_dir.mkdir(parents=True)
    
    # Create a minimal metrics file
    mock_data = [
        {
            "subject_id": "sub-001",
            "time_point": "acute",
            "global_efficiency": 0.45,
            "modularity": 0.32,
            "cognitive_score": 85.0
        },
        {
            "subject_id": "sub-001",
            "time_point": "chronic",
            "global_efficiency": 0.48,
            "modularity": 0.35,
            "cognitive_score": 90.0
        }
    ]
    
    metrics_file = processed_dir / "connectivity_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(mock_data, f)
    
    return processed_dir

def test_is_synthetic_flag_in_output(mock_data_dir, tmp_path):
    """Test that output JSON includes is_synthetic flag when in synthetic mode."""
    # Enable synthetic mode
    set_synthetic_mode(True)
    
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    # Run analysis
    results = run_statistical_analysis(mock_data_dir, results_dir)
    
    # Verify flag is present
    assert "is_synthetic" in results
    assert results["is_synthetic"] is True
    
    assert "methodology_validation_mode" in results
    assert results["methodology_validation_mode"] is True

def test_is_synthetic_flag_false_in_real_mode(mock_data_dir, tmp_path):
    """Test that output JSON includes is_synthetic flag as False in real mode."""
    # Ensure synthetic mode is off
    set_synthetic_mode(False)
    
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    # Run analysis
    results = run_statistical_analysis(mock_data_dir, results_dir)
    
    # Verify flag is present and False
    assert "is_synthetic" in results
    assert results["is_synthetic"] is False
    
    assert "methodology_validation_mode" in results
    assert results["methodology_validation_mode"] is False

def test_output_file_contains_synthetic_flag(mock_data_dir, tmp_path):
    """Test that the saved JSON file contains the is_synthetic flag."""
    set_synthetic_mode(True)
    
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    
    run_statistical_analysis(mock_data_dir, results_dir)
    
    output_file = results_dir / "model_results.json"
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        saved_data = json.load(f)
    
    assert "is_synthetic" in saved_data
    assert saved_data["is_synthetic"] is True