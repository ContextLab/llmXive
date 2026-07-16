import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from data_models import PolymerRecord
from power_analysis import check_dataset_power, run_power_analysis_from_csv

@pytest.fixture
def sample_records():
    """Create a list of sample PolymerRecord objects."""
    return [
        PolymerRecord(
            id=f"rec_{i}",
            smiles="CC(=O)OC",  # Simple ester
            temperature=25.0,
            ph=7.0,
            uv_intensity=100.0,
            degradation_pathway="hydrolysis"
        )
        for i in range(10)
    ]

@pytest.fixture
def large_sample_records():
    """Create a list of 200 sample records to pass power analysis."""
    return [
        PolymerRecord(
            id=f"rec_{i}",
            smiles="CC(=O)OC",
            temperature=25.0,
            ph=7.0,
            uv_intensity=100.0,
            degradation_pathway="hydrolysis"
        )
        for i in range(200)
    ]

def test_check_dataset_power_sufficient():
    """Test that a sufficient dataset size returns True."""
    assert check_dataset_power(150) is True
    assert check_dataset_power(200) is True
    assert check_dataset_power(1000) is True

def test_check_dataset_power_insufficient():
    """Test that an insufficient dataset size returns False."""
    assert check_dataset_power(149) is False
    assert check_dataset_power(100) is False
    assert check_dataset_power(0) is False

def test_run_power_analysis_from_csv_sufficient(large_sample_records, tmp_path):
    """Test power analysis when dataset size is sufficient."""
    # Patch the warning file path to use a temporary directory
    with patch('power_analysis.WARNING_FILE_PATH', str(tmp_path / "warning.txt")):
        result = run_power_analysis_from_csv(large_sample_records)
    
    assert result['dataset_size'] == 200
    assert result['is_powered'] is True
    assert result['warning_generated'] is False
    assert result['warning_path'] is None
    # Ensure no warning file was created
    assert not os.path.exists(str(tmp_path / "warning.txt"))

def test_run_power_analysis_from_csv_insufficient(sample_records, tmp_path):
    """Test power analysis when dataset size is insufficient."""
    warning_file = tmp_path / "warning.txt"
    with patch('power_analysis.WARNING_FILE_PATH', str(warning_file)):
        result = run_power_analysis_from_csv(sample_records)
    
    assert result['dataset_size'] == 10
    assert result['is_powered'] is False
    assert result['warning_generated'] is True
    assert result['warning_path'] == str(warning_file.resolve())
    
    # Verify the warning file was created and contains expected content
    assert warning_file.exists()
    content = warning_file.read_text()
    assert "POWER ANALYSIS WARNING" in content
    assert "Dataset size (10)" in content
    assert "below the minimum threshold (150)" in content
