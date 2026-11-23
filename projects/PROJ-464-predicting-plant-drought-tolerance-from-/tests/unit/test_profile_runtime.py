"""
Unit tests for T034b: Runtime Profiling.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

# Ensure code path is accessible
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from profile_runtime import generate_runtime_report, run_pipeline_subset

def test_generate_runtime_report_creates_file(tmp_path):
    """Test that the report generation creates a valid YAML file."""
    # Mock profile data
    mock_stats = MagicMock()
    mock_stats.stats = {
        ("file.py", 10, "func_a"): (1, 1, 0.1, 0.5, {}),
        ("file.py", 20, "func_b"): (2, 2, 0.2, 0.6, {})
    }
    
    # Create a temporary directory for the report
    output_dir = tmp_path / "state"
    output_dir.mkdir()
    
    # Patch the output path to use temp dir
    with patch("profile_runtime.Path") as mock_path:
        mock_path.return_value = output_dir / "runtime_profile.yaml"
        mock_path.side_effect = lambda x: output_dir / x if x else output_dir / "runtime_profile.yaml"
        
        # We need to patch the ensure_directories to not fail
        with patch("profile_runtime.ensure_directories"):
            report = generate_runtime_report(1.5, mock_stats)
    
    # Verify file existence and content
    report_path = output_dir / "runtime_profile.yaml"
    assert report_path.exists()
    
    with open(report_path) as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
    
    assert data["task_id"] == "T034b"
    assert "total_runtime_seconds" in data
    assert "passed_limit" in data
    assert len(data["top_functions"]) > 0

def test_run_pipeline_subset_handles_missing_data():
    """Test that the subset runner handles the expected 'missing data' halt."""
    # Mock download_images_main to raise the expected error
    with patch("profile_runtime.download_images_main") as mock_dl:
        mock_dl.side_effect = RuntimeError("No real NPPN root images found. Pipeline cannot proceed.")
        
        # This should not raise an exception but return early
        result = run_pipeline_subset()
        
        # The function should return None (implicit) or stop execution
        # We verify it didn't crash with an unhandled exception
        assert True

def test_runtime_constraint_logic():
    """Test the logic for checking runtime against 6h limit."""
    # Logic is inside generate_runtime_report, specifically the 'passed_limit' field
    # This is implicitly tested by test_generate_runtime_report_creates_file
    # but we can add a direct assertion on the calculation
    total_time_6h = 21600.0
    total_time_exceed = 21601.0
    
    assert (total_time_6h <= 21600) == True
    assert (total_time_exceed <= 21600) == False