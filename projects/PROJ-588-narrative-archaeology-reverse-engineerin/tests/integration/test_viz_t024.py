"""
Integration test for T024: Visualization of Early vs. Late ROI comparison.
Verifies that plot_early_late_roi_comparison produces the expected output file.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Ensure we can import from the project root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.viz import plot_early_late_roi_comparison
import code.config as config

@pytest.fixture
def mock_stats_file(tmp_path):
    """Create a mock group_rsa_stats.json file for testing."""
    stats = {
        "mPFC": {
            "early_late": 0.45,
            "early_early": 0.20
        },
        "hippocampus": {
            "early_late": 0.52,
            "early_early": 0.18
        },
        "PCC": {
            "early_late": 0.38,
            "early_early": 0.25
        },
        "lateral_temporal": {
            "early_late": 0.30,
            "early_early": 0.22
        }
    }
    stats_file = tmp_path / "group_rsa_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f)
    return str(stats_file)

@pytest.fixture
def mock_output_dir(tmp_path):
    """Create a temporary directory for output."""
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    return str(output_dir)

def test_plot_early_late_roi_comparison_creates_file(mock_stats_file, mock_output_dir):
    """Test that the visualization function creates the output PNG file."""
    output_path = Path(mock_output_dir) / "rsa_heatmaps.png"
    
    # Run the function
    plot_early_late_roi_comparison(mock_stats_file, str(output_path))
    
    # Verify the file exists and has non-zero size
    assert output_path.exists(), f"Output file not created at {output_path}"
    assert output_path.stat().st_size > 0, "Output file is empty"
    
    # Verify it's a valid PNG (check magic bytes)
    with open(output_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n', "File does not appear to be a valid PNG"

def test_plot_early_late_roi_comparison_missing_rois(mock_stats_file, mock_output_dir):
    """Test behavior when some target ROIs are missing from stats."""
    # Modify stats to remove some ROIs
    stats = {
        "mPFC": {
            "early_late": 0.45,
            "early_early": 0.20
        },
        "unknown_roi": {
            "early_late": 0.30,
            "early_early": 0.25
        }
    }
    stats_file = Path(mock_output_dir) / "partial_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f)
    
    output_path = Path(mock_output_dir) / "partial_rsa.png"
    
    # Should still create a plot with available ROIs
    plot_early_late_roi_comparison(str(stats_file), str(output_path))
    
    assert output_path.exists(), "Output file should be created even with partial data"
    assert output_path.stat().st_size > 0, "Output file should not be empty"

def test_plot_early_late_roi_comparison_no_valid_data(mock_output_dir):
    """Test error handling when no valid data is found."""
    # Create stats with missing keys
    stats = {
        "mPFC": {
            "wrong_key": 0.45
        }
    }
    stats_file = Path(mock_output_dir) / "bad_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f)
    
    output_path = Path(mock_output_dir) / "bad_rsa.png"
    
    # Should raise ValueError
    with pytest.raises(ValueError, match="No valid data found"):
        plot_early_late_roi_comparison(str(stats_file), str(output_path))
