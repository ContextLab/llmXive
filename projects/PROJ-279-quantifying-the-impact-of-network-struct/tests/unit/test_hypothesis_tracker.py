import pytest
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis_tracker import (
    load_regression_results,
    load_descriptor_availability,
    determine_hypothesis_status,
    save_hypothesis_status,
    main
)
from config.env_config import get_processed_dir

@pytest.fixture
def mock_processed_dir(tmp_path):
    # Create a mock processed directory structure
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    with patch('config.env_config.get_processed_dir') as mock_get:
        mock_get.return_value = tmp_path
        yield tmp_path

def test_load_regression_results_file_not_found(mock_processed_dir):
    # Ensure the file doesn't exist
    assert not (mock_processed_dir / "results" / "regression_metrics.json").exists()
    result = load_regression_results()
    assert result is None

def test_load_regression_results_success(mock_processed_dir):
    # Create a mock regression results file
    results_path = mock_processed_dir / "results" / "regression_metrics.json"
    mock_data = {"status": "success", "r2": 0.85}
    with open(results_path, 'w') as f:
        json.dump(mock_data, f)
    
    result = load_regression_results()
    assert result is not None
    assert result["status"] == "success"
    assert result["r2"] == 0.85

def test_load_descriptor_availability_no_file(mock_processed_dir):
    result = load_descriptor_availability()
    assert all(v == False for v in result.values())

def test_load_descriptor_availability_success(mock_processed_dir):
    # Create a mock descriptors CSV
    descriptors_path = mock_processed_dir / "descriptors.csv"
    data = {
        "config_id": [1, 2],
        "ring_3": [0.1, 0.2],
        "ring_4": [0.3, 0.4],
        "q6": [0.5, 0.6],
        "clustering_coeff": [0.7, 0.8],
        "vdos_integral": [0.9, 1.0],
        "k": [10.0, 11.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(descriptors_path, index=False)
    
    result = load_descriptor_availability()
    assert result["ring_statistics"] is True
    assert result["steinhardt_q6"] is True
    assert result["clustering_coefficient"] is True
    assert result["vdos_available"] is True
    assert result["k_available"] is True

def test_determine_hypothesis_status_regression_success(mock_processed_dir):
    regression_results = {"status": "success"}
    descriptor_availability = {
        "ring_statistics": True,
        "vdos_available": True,
        "k_available": True
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    assert status["H-001"]["status"] == "TESTED"
    assert status["H-002"]["status"] == "TESTED"
    assert status["H-003"]["status"] == "TESTED"
    assert status["H-004"]["status"] == "TESTED"

def test_determine_hypothesis_status_regression_missing_k(mock_processed_dir):
    regression_results = None # No regression results
    descriptor_availability = {
        "ring_statistics": True,
        "vdos_available": False,
        "k_available": False
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    # H-001/H-002 should be UNTESTABLE because k is missing
    assert status["H-001"]["status"] == "UNTESTABLE"
    assert status["H-002"]["status"] == "UNTESTABLE"
    
    # H-003 should be TESTED (ring stats exist)
    assert status["H-003"]["status"] == "TESTED"
    
    # H-004 should be UNTESTABLE (regression didn't run, so importance not computed)
    assert status["H-004"]["status"] == "UNTESTABLE"

def test_determine_hypothesis_status_no_ring_stats(mock_processed_dir):
    regression_results = {"status": "success"}
    descriptor_availability = {
        "ring_statistics": False,
        "vdos_available": True,
        "k_available": True
    }
    
    status = determine_hypothesis_status(regression_results, descriptor_availability)
    
    assert status["H-003"]["status"] == "FAILED"
    assert status["H-004"]["status"] == "FAILED"

def test_save_hypothesis_status(mock_processed_dir):
    status = {
        "H-001": {"status": "TESTED", "reason": "Test"},
        "H-002": {"status": "TESTED", "reason": "Test"},
        "H-003": {"status": "TESTED", "reason": "Test"},
        "H-004": {"status": "TESTED", "reason": "Test"}
    }
    
    output_path = save_hypothesis_status(status)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded_status = json.load(f)
    
    assert loaded_status == status