"""
Tests for T018: Power Analysis.
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from power_analysis import load_split_indices, calculate_power_status, main

def test_load_split_indices_valid():
    """Test loading valid split indices."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"train": [1, 2, 3], "val": [4], "test": [5, 6]}, f)
        temp_path = f.name
    
    try:
        data = load_split_indices(temp_path)
        assert "test" in data
        assert len(data["test"]) == 2
    finally:
        os.unlink(temp_path)

def test_load_split_indices_missing_file():
    """Test loading missing split indices raises error."""
    with pytest.raises(FileNotFoundError):
        load_split_indices("nonexistent.json")

def test_calculate_power_status_low():
    """Test power status for small sample size."""
    assert calculate_power_status(10) == "low_power"
    assert calculate_power_status(49) == "low_power"

def test_calculate_power_status_high():
    """Test power status for sufficient sample size."""
    assert calculate_power_status(50) == "high_power"
    assert calculate_power_status(100) == "high_power"
    assert calculate_power_status(1000) == "high_power"

def test_main_execution(tmp_path):
    """Test the main function writes output correctly."""
    input_data = {
        "train": list(range(80)),
        "val": list(range(80, 90)),
        "test": list(range(90, 100))
    }
    
    input_file = tmp_path / "split_indices.json"
    with open(input_file, 'w') as f:
        json.dump(input_data, f)
    
    output_file = tmp_path / "power_analysis.json"
    
    # Mock sys.argv to simulate command line arguments
    sys.argv = ["power_analysis.py", "--input", str(input_file), "--output", str(output_file)]
    
    # Run main
    result = main()
    
    assert result == 0
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        output_data = json.load(f)
    
    assert "n" in output_data
    assert output_data["n"] == 10
    assert "power_status" in output_data
    assert output_data["power_status"] == "high_power"
    assert output_data["alpha"] == 0.05
    assert output_data["target_power"] == 0.8
    assert output_data["effect_size"] == 0.5