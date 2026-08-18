"""
Unit tests for Data Source Adapter (T009) and Real Data Validator (T009b)
"""
import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.data_source_adapter import (
    get_project_root,
    check_real_data,
    check_mock_data,
    copy_mock_to_studies,
    run_data_source_adapter
)
from data.real_data_validator import (
    count_studies_in_csv,
    write_status_file,
    validate_real_data
)

@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    temp_dir = tempfile.mkdtemp()
    # Create necessary subdirectories
    os.makedirs(os.path.join(temp_dir, "data", "raw"))
    os.makedirs(os.path.join(temp_dir, "data", "processed"))
    os.makedirs(os.path.join(temp_dir, "state", "projects"))
    os.makedirs(os.path.join(temp_dir, "code", "config"))
    
    # Create a dummy config file
    config_path = os.path.join(temp_dir, "code", "config", "config.yaml")
    with open(config_path, 'w') as f:
        f.write("seed: 42\n")
    
    # Mock get_project_root to return temp_dir
    import data.data_source_adapter as adapter_module
    import data.real_data_validator as validator_module
    import utils.config as config_module
    
    original_get_project_root = config_module.get_project_root
    config_module.get_project_root = lambda: Path(temp_dir)
    adapter_module.get_project_root = lambda: Path(temp_dir)
    validator_module.get_project_root = lambda: Path(temp_dir)
    
    yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)
    config_module.get_project_root = original_get_project_root

def test_check_real_data_no_file(temp_project_dir):
    """Test check_real_data when no file exists."""
    assert check_real_data() is False

def test_check_real_data_with_file(temp_project_dir):
    """Test check_real_data when file exists."""
    studies_path = temp_project_dir / "data" / "raw" / "studies.csv"
    studies_path.touch()
    assert check_real_data() is True

def test_check_mock_data_no_files(temp_project_dir):
    """Test check_mock_data when no mock files exist."""
    assert check_mock_data() is None

def test_check_mock_data_with_fallback(temp_project_dir):
    """Test check_mock_data when fallback file exists."""
    fallback_path = temp_project_dir / "data" / "raw" / "mock_studies_fallback.csv"
    fallback_path.touch()
    assert check_mock_data() == fallback_path

def test_copy_mock_to_studies(temp_project_dir):
    """Test copying mock data to studies.csv."""
    mock_path = temp_project_dir / "data" / "raw" / "mock_studies_fallback.csv"
    with open(mock_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["author", "year", "tract", "r", "n", "qualitative_desc"])
        writer.writerow(["Test", 2023, "Tract", 0.5, 100, "Test desc"])
    
    copy_mock_to_studies(mock_path)
    
    target_path = temp_project_dir / "data" / "raw" / "studies.csv"
    assert target_path.exists()
    
    with open(target_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["author"] == "Test"

def test_validate_real_data_insufficient_count(temp_project_dir):
    """Test validate_real_data with N < 10."""
    studies_path = temp_project_dir / "data" / "raw" / "studies.csv"
    with open(studies_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["author", "year", "tract", "r", "n", "qualitative_desc"])
        writer.writeheader()
        writer.writerow({"author": "Test", "year": 2023, "tract": "Tract", "r": 0.5, "n": 100, "qualitative_desc": "Desc"})
    
    status = validate_real_data(studies_path)
    
    assert status["valid"] is True
    assert status["n"] == 1
    assert status["threshold_met"] is False
    assert status["error"] is None

def test_validate_real_data_sufficient_count(temp_project_dir):
    """Test validate_real_data with N >= 10."""
    studies_path = temp_project_dir / "data" / "raw" / "studies.csv"
    with open(studies_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["author", "year", "tract", "r", "n", "qualitative_desc"])
        writer.writeheader()
        for i in range(10):
            writer.writerow({"author": f"Test{i}", "year": 2023, "tract": "Tract", "r": 0.5, "n": 100, "qualitative_desc": "Desc"})
    
    status = validate_real_data(studies_path)
    
    assert status["valid"] is True
    assert status["n"] == 10
    assert status["threshold_met"] is True
    assert status["error"] is None

def test_validate_real_data_zero_count(temp_project_dir):
    """Test validate_real_data with N = 0."""
    studies_path = temp_project_dir / "data" / "raw" / "studies.csv"
    with open(studies_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["author", "year", "tract", "r", "n", "qualitative_desc"])
        writer.writeheader()
    
    status = validate_real_data(studies_path)
    
    assert status["valid"] is False
    assert status["n"] == 0
    assert status["threshold_met"] is False
    assert "No studies found" in status["error"]