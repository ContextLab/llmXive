import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.clean import calculate_coverage_rate, METRICS_FILE, TOTAL_RECORDS_FILE

@pytest.fixture
def temp_metrics_dir():
    """Create a temporary directory for data/processed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Mock the global paths
        with patch('data.clean.DATA_PROCESSED_DIR', tmpdir_path), \
             patch('data.clean.TOTAL_RECORDS_FILE', tmpdir_path / "total_records_count.json"), \
             patch('data.clean.METRICS_FILE', tmpdir_path / "metrics.json"):
            yield tmpdir_path

def test_coverage_rate_calculation_success(temp_metrics_dir):
    """Test that coverage rate is calculated correctly when data exists."""
    # Prepare mock data for T008 output
    mock_counts = {
        "total_available": 1000,
        "total_merged": 800,
        "source": "FAO+WB",
        "years": [2000, 2020]
    }

    # Write mock T008 file
    with open(TOTAL_RECORDS_FILE, 'w') as f:
        json.dump(mock_counts, f)

    # Run function
    result = calculate_coverage_rate()

    # Assertions
    assert result["coverage_rate"] == 0.8
    assert result["total_available"] == 1000
    assert result["total_merged"] == 800

    # Verify file was written
    assert METRICS_FILE.exists()
    with open(METRICS_FILE, 'r') as f:
        saved_metrics = json.load(f)
    assert saved_metrics["coverage_rate"] == 0.8

def test_coverage_rate_zero_available(temp_metrics_dir):
    """Test handling of zero total available records."""
    mock_counts = {
        "total_available": 0,
        "total_merged": 0,
        "source": "FAO+WB",
        "years": []
    }

    with open(TOTAL_RECORDS_FILE, 'w') as f:
        json.dump(mock_counts, f)

    result = calculate_coverage_rate()

    assert result["coverage_rate"] == 0.0
    assert result["total_available"] == 0

def test_coverage_rate_missing_file(temp_metrics_dir):
    """Test that FileNotFoundError is raised if T008 file is missing."""
    # Ensure file does not exist
    if TOTAL_RECORDS_FILE.exists():
        TOTAL_RECORDS_FILE.unlink()

    with pytest.raises(FileNotFoundError, match="Total records count file not found"):
        calculate_coverage_rate()