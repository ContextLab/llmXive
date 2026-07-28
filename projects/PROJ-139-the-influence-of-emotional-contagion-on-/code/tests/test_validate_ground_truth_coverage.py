"""
Tests for T053: Validate Ground Truth Coverage
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.validate_ground_truth_coverage import (
    load_ground_truth_stats,
    validate_coverage,
    save_report,
    main
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_stats_file(temp_dir):
    """Create a mock ground_truth_stats.json file."""
    stats = {
        "total_dataset_count": 1000,
        "valid_dataset_count": 350,
        "valid_thread_percentage": 35.0
    }
    stats_path = temp_dir / "ground_truth_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f)
    return stats_path

@pytest.fixture
def mock_low_coverage_stats(temp_dir):
    """Create a mock ground_truth_stats.json with low coverage."""
    stats = {
        "total_dataset_count": 1000,
        "valid_dataset_count": 200,
        "valid_thread_percentage": 20.0
    }
    stats_path = temp_dir / "ground_truth_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f)
    return stats_path

def test_load_ground_truth_stats_success(mock_stats_file):
    """Test successful loading of ground truth stats."""
    with patch('analysis.validate_ground_truth_coverage.get_config') as mock_config:
        mock_config.return_value.dataset_paths.processed = str(mock_stats_file.parent)
        
        stats = load_ground_truth_stats()
        assert stats is not None
        assert stats["total_dataset_count"] == 1000
        assert stats["valid_thread_percentage"] == 35.0

def test_load_ground_truth_stats_missing_file(temp_dir):
    """Test loading when file doesn't exist."""
    with patch('analysis.validate_ground_truth_coverage.get_config') as mock_config:
        mock_config.return_value.dataset_paths.processed = str(temp_dir)
        
        stats = load_ground_truth_stats()
        assert stats is None

def test_validate_coverage_pass():
    """Test validation with sufficient coverage."""
    stats = {
        "total_dataset_count": 1000,
        "valid_dataset_count": 350,
        "valid_thread_percentage": 35.0
    }
    
    report = validate_coverage(stats)
    assert report["status"] == "pass"
    assert report["valid_thread_percentage"] == 35.0
    assert report["threshold_met"] is True
    assert len(report["recommendations"]) > 0

def test_validate_coverage_fail():
    """Test validation with insufficient coverage."""
    stats = {
        "total_dataset_count": 1000,
        "valid_dataset_count": 200,
        "valid_thread_percentage": 20.0
    }
    
    report = validate_coverage(stats)
    assert report["status"] == "fail"
    assert report["valid_thread_percentage"] == 20.0
    assert report["threshold_met"] is False
    # Should have recommendations for improvement
    assert any("below the required threshold" in rec for rec in report["recommendations"])

def test_validate_coverage_edge_case_30_percent():
    """Test validation exactly at the 30% threshold."""
    stats = {
        "total_dataset_count": 1000,
        "valid_dataset_count": 300,
        "valid_thread_percentage": 30.0
    }
    
    report = validate_coverage(stats)
    assert report["status"] == "pass"
    assert report["threshold_met"] is True

def test_save_report(temp_dir):
    """Test saving report to file."""
    report = {
        "status": "pass",
        "valid_thread_percentage": 35.0,
        "recommendations": ["Test recommendation"]
    }
    
    output_path = temp_dir / "test_report.json"
    save_report(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["status"] == "pass"
    assert saved_report["valid_thread_percentage"] == 35.0

@patch('analysis.validate_ground_truth_coverage.get_config')
@patch('analysis.validate_ground_truth_coverage.load_ground_truth_stats')
@patch('analysis.validate_ground_truth_coverage.validate_coverage')
@patch('analysis.validate_ground_truth_coverage.save_report')
def test_main_success(
    mock_save, 
    mock_validate, 
    mock_load, 
    mock_config, 
    temp_dir,
    mock_stats_file
):
    """Test main function with successful validation."""
    # Setup mocks
    mock_config.return_value.dataset_paths.processed = str(mock_stats_file.parent)
    mock_config.return_value.dataset_paths.state = str(temp_dir)
    mock_load.return_value = {
        "total_dataset_count": 1000,
        "valid_dataset_count": 350,
        "valid_thread_percentage": 35.0
    }
    mock_validate.return_value = {
        "status": "pass",
        "valid_thread_percentage": 35.0,
        "recommendations": []
    }
    
    result = main()
    assert result == 0
    mock_load.assert_called_once()
    mock_validate.assert_called_once()
    mock_save.assert_called_once()

@patch('analysis.validate_ground_truth_coverage.get_config')
@patch('analysis.validate_ground_truth_coverage.load_ground_truth_stats')
def test_main_missing_stats(mock_load, mock_config, temp_dir):
    """Test main function when stats file is missing."""
    mock_config.return_value.dataset_paths.processed = str(temp_dir)
    mock_load.return_value = None
    
    result = main()
    assert result == 1
    mock_load.assert_called_once()