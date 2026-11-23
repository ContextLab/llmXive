import json
import logging
from pathlib import Path
import pytest
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import validate_sample_size

@pytest.fixture
def temp_output_dir(tmp_path):
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    return str(processed_dir)

def test_validate_sample_size_low_count(temp_output_dir):
    """Test validation when count is below 30."""
    count = 20
    output_path = Path(temp_output_dir) / "sample_size_report.json"
    
    result = validate_sample_size(count, str(output_path))
    
    assert result["count"] == 20
    assert result["validation_status"] == "proceed"
    assert "outside" in result["message"].lower()
    
    # Verify file exists
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert data["count"] == 20
    assert data["validation_status"] == "proceed"

def test_validate_sample_size_high_count(temp_output_dir):
    """Test validation when count is above 45."""
    count = 50
    output_path = Path(temp_output_dir) / "sample_size_report.json"
    
    result = validate_sample_size(count, str(output_path))
    
    assert result["count"] == 50
    assert result["validation_status"] == "proceed"
    assert "outside" in result["message"].lower()

def test_validate_sample_size_valid_count(temp_output_dir):
    """Test validation when count is within 30-45."""
    count = 35
    output_path = Path(temp_output_dir) / "sample_size_report.json"
    
    result = validate_sample_size(count, str(output_path))
    
    assert result["count"] == 35
    assert result["validation_status"] == "proceed"
    assert "within" in result["message"].lower()

def test_validate_sample_size_boundary_low(temp_output_dir):
    """Test validation at lower boundary (30)."""
    count = 30
    output_path = Path(temp_output_dir) / "sample_size_report.json"
    
    result = validate_sample_size(count, str(output_path))
    
    assert result["count"] == 30
    assert result["validation_status"] == "proceed"
    assert "within" in result["message"].lower()

def test_validate_sample_size_boundary_high(temp_output_dir):
    """Test validation at upper boundary (45)."""
    count = 45
    output_path = Path(temp_output_dir) / "sample_size_report.json"
    
    result = validate_sample_size(count, str(output_path))
    
    assert result["count"] == 45
    assert result["validation_status"] == "proceed"
    assert "within" in result["message"].lower()
