"""
Unit tests for T013d: set_gt_flag.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data.set_gt_flag import check_ground_truth_availability, set_gt_flag
from utils.config import get_hyperparameter, initialize_paths

def test_check_ground_truth_availability_file_exists():
    """Test that check_ground_truth_availability returns True when file exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gt_file = Path(tmpdir) / "ground_truth_annotations.json"
        gt_file.write_text("{}")
        
        result = check_ground_truth_availability(gt_file)
        assert result is True

def test_check_ground_truth_availability_file_missing():
    """Test that check_ground_truth_availability returns False when file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gt_file = Path(tmpdir) / "ground_truth_annotations.json"
        
        result = check_ground_truth_availability(gt_file)
        assert result is False

def test_check_ground_truth_availability_is_directory():
    """Test that check_ground_truth_availability returns False if path is a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gt_file = Path(tmpdir) / "ground_truth_annotations.json"
        gt_file.mkdir()
        
        result = check_ground_truth_availability(gt_file)
        assert result is False

@patch('data.set_gt_flag.get_path')
@patch('data.set_gt_flag.initialize_paths')
def test_set_gt_flag_available(mock_init, mock_get_path, tmp_path):
    """Test set_gt_flag when ground truth file exists."""
    # Setup mock paths
    mock_raw_path = tmp_path / "raw" / "guava"
    mock_raw_path.mkdir(parents=True)
    gt_file = mock_raw_path / "ground_truth_annotations.json"
    gt_file.write_text("{}")
    
    mock_get_path.return_value = mock_raw_path.parent / "guava" # get_path("raw_guava")
    
    # Reset config state
    initialize_paths()
    
    # Run function
    result = set_gt_flag()
    
    assert result is True
    assert get_hyperparameter("PERCEPTION_GT_AVAILABLE") is True

@patch('data.set_gt_flag.get_path')
@patch('data.set_gt_flag.initialize_paths')
def test_set_gt_flag_unavailable(mock_init, mock_get_path, tmp_path):
    """Test set_gt_flag when ground truth file does not exist."""
    # Setup mock paths (directory exists, file does not)
    mock_raw_path = tmp_path / "raw" / "guava"
    mock_raw_path.mkdir(parents=True)
    
    mock_get_path.return_value = mock_raw_path.parent / "guava"
    
    # Reset config state
    initialize_paths()
    
    # Run function
    result = set_gt_flag()
    
    assert result is False
    assert get_hyperparameter("PERCEPTION_GT_AVAILABLE") is False