"""
Unit tests for real_data_validator.py (T009b)
"""
import json
import csv
import os
import tempfile
from pathlib import Path
import pytest

# Mock the project root for testing
class MockProjectRoot:
    def __init__(self, tmp_path):
        self.tmp_path = tmp_path
        
    def __truediv__(self, other):
        return self.tmp_path / other

@pytest.fixture
def mock_project_root(tmp_path):
    # Create necessary directory structure
    (tmp_path / "data" / "raw").mkdir(parents=True)
    (tmp_path / "data" / "processed").mkdir(parents=True)
    return MockProjectRoot(tmp_path)

def test_count_studies_in_csv(mock_project_root):
    """Test counting studies in a CSV file."""
    # Create a mock CSV file
    csv_path = mock_project_root.tmp_path / "data" / "raw" / "studies.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
        for i in range(5):
            writer.writerow({
                'author': f'Author{i}',
                'year': 2020 + i,
                'tract': 'tract1',
                'r': 0.5,
                'n': 100
            })
    
    # Import the function (we'll need to mock get_project_root)
    from code.data.real_data_validator import count_studies_in_csv
    count = count_studies_in_csv(csv_path)
    assert count == 5

def test_count_studies_in_empty_csv(mock_project_root):
    """Test counting studies in an empty CSV file (header only)."""
    csv_path = mock_project_root.tmp_path / "data" / "raw" / "studies.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
    
    from code.data.real_data_validator import count_studies_in_csv
    count = count_studies_in_csv(csv_path)
    assert count == 0

def test_count_studies_in_nonexistent_csv(mock_project_root):
    """Test counting studies in a non-existent CSV file."""
    csv_path = mock_project_root.tmp_path / "data" / "raw" / "nonexistent.csv"
    
    from code.data.real_data_validator import count_studies_in_csv
    count = count_studies_in_csv(csv_path)
    assert count == 0

def test_write_status_file(mock_project_root):
    """Test writing the status file."""
    from code.data.real_data_validator import write_status_file
    
    status = {
        "valid": True,
        "n": 15,
        "threshold_met": True,
        "error": None
    }
    
    write_status_file(status)
    
    # Check if the file was created
    output_path = mock_project_root.tmp_path / "data" / "processed" / "real_data_status.json"
    assert output_path.exists()
    
    # Check the content
    with open(output_path, 'r', encoding='utf-8') as f:
        written_status = json.load(f)
    
    assert written_status == status

def test_validate_real_data_above_threshold(mock_project_root):
    """Test validation with N >= 10."""
    # Create a mock CSV file with 15 studies
    csv_path = mock_project_root.tmp_path / "data" / "raw" / "studies.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
        for i in range(15):
            writer.writerow({
                'author': f'Author{i}',
                'year': 2020 + i,
                'tract': 'tract1',
                'r': 0.5,
                'n': 100
            })
    
    from code.data.real_data_validator import validate_real_data
    status = validate_real_data(csv_path)
    
    assert status["valid"] is True
    assert status["n"] == 15
    assert status["threshold_met"] is True
    assert status["error"] is None

def test_validate_real_data_below_threshold(mock_project_root):
    """Test validation with N < 10."""
    # Create a mock CSV file with 5 studies
    csv_path = mock_project_root.tmp_path / "data" / "raw" / "studies.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
        for i in range(5):
            writer.writerow({
                'author': f'Author{i}',
                'year': 2020 + i,
                'tract': 'tract1',
                'r': 0.5,
                'n': 100
            })
    
    from code.data.real_data_validator import validate_real_data
    status = validate_real_data(csv_path)
    
    assert status["valid"] is True
    assert status["n"] == 5
    assert status["threshold_met"] is False
    assert status["error"] is None

def test_validate_real_data_zero_studies(mock_project_root):
    """Test validation with N = 0."""
    # Create a mock CSV file with header only
    csv_path = mock_project_root.tmp_path / "data" / "raw" / "studies.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['author', 'year', 'tract', 'r', 'n'])
        writer.writeheader()
    
    from code.data.real_data_validator import validate_real_data
    status = validate_real_data(csv_path)
    
    assert status["valid"] is False
    assert status["n"] == 0
    assert status["threshold_met"] is False
    assert status["error"] == "No studies found in real data."