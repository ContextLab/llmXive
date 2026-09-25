import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import shutil

from download import count_unique_planets, save_count_report, report_sample_size

@pytest.fixture
def temp_metadata_csv():
    """Creates a temporary metadata.csv for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    metadata_path = temp_dir / "metadata.csv"
    
    # Create a dummy CSV with planet names
    data = [
        {"planet_name": "Kepler-18b", "temperature": 1200, "metallicity": 0.1},
        {"planet_name": "HD-209458b", "temperature": 1400, "metallicity": 0.0},
        {"planet_name": "Kepler-18b", "temperature": 1200, "metallicity": 0.1}, # Duplicate
        {"planet_name": "Wool-42c", "temperature": 900, "metallicity": -0.5},
    ]
    df = pd.DataFrame(data)
    df.to_csv(metadata_path, index=False)
    
    yield metadata_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_count_unique_planets(temp_metadata_csv):
    """Tests that count_unique_planets correctly counts unique planets."""
    count = count_unique_planets(str(temp_metadata_csv))
    assert count == 3, f"Expected 3 unique planets, got {count}"

def test_save_count_report(temp_metadata_csv):
    """Tests that save_count_report writes the correct JSON."""
    count = 3
    temp_dir = temp_metadata_csv.parent
    output_path = temp_dir / "count_report.json"
    
    save_count_report(count, str(output_path))
    
    assert output_path.exists(), "count_report.json was not created"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["count"] == 3, f"Expected count 3, got {data['count']}"

def test_report_sample_size_within_range(temp_metadata_csv):
    """Tests report_sample_size when count is within 30-45 range."""
    # Simulate a count within range
    count = 35
    temp_dir = temp_metadata_csv.parent
    output_path = temp_dir / "sample_size_report.json"
    
    result = report_sample_size(count, str(output_path))
    
    assert result["count"] == 35
    assert result["count_within_range"] is True
    assert result["test_failure"] is False
    assert "note" in result

def test_report_sample_size_outside_range(temp_metadata_csv):
    """Tests report_sample_size when count is outside 30-45 range."""
    # Simulate a count outside range
    count = 20
    temp_dir = temp_metadata_csv.parent
    output_path = temp_dir / "sample_size_report.json"
    
    result = report_sample_size(count, str(output_path))
    
    assert result["count"] == 20
    assert result["count_within_range"] is False
    assert result["test_failure"] is True