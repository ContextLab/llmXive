import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
# Note: In a real test runner, we might need to adjust sys.path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from code_01_data_acquisition import step_2a_download_and_validate_defect_dataset, get_project_root, ensure_output_directories, load_json_file, save_json_file, save_to_csv, load_csv_to_dicts

# Mock the get_project_root to use a temp directory for testing
# We cannot easily patch the function inside the module if it's not designed for it,
# so we will simulate the file structure.

@pytest.fixture
def temp_project_dir():
    """Creates a temporary directory structure mimicking the project."""
    temp_dir = tempfile.mkdtemp()
    # Create expected subdirectories
    (Path(temp_dir) / 'data' / 'raw').mkdir(parents=True)
    (Path(temp_dir) / 'data' / 'state').mkdir(parents=True)
    (Path(temp_dir) / 'data' / 'processed').mkdir(parents=True)
    return temp_dir

@pytest.fixture
def mock_pristine_file(temp_project_dir):
    """Creates a mock pristine_structures.csv file."""
    pristine_path = Path(temp_project_dir) / 'data' / 'raw' / 'pristine_structures.csv'
    with open(pristine_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['material_id', 'formula', 'structure'])
        writer.writeheader()
        writer.writerow({'material_id': 'mp-1', 'formula': 'C', 'structure': 'graphene'})
    return pristine_path

def test_t011a_missing_dependency(temp_project_dir, monkeypatch):
    """Test T011a when T010a output (pristine_structures.csv) is missing."""
    # We need to mock get_project_root to return our temp dir
    # Since the function is defined in the module, we patch it
    import code_01_data_acquisition as mod
    
    original_get_root = mod.get_project_root
    mod.get_project_root = lambda: Path(temp_project_dir)
    
    try:
        result = step_2a_download_and_validate_defect_dataset()
        
        assert result['valid'] == False
        assert 'Dependency failed' in result['reason']
        
        # Check that validation file was written
        validation_path = Path(temp_project_dir) / 'data' / 'state' / 'source_validation.json'
        assert validation_path.exists()
        
        # Check that the defect dataset file was created (even if empty)
        dataset_path = Path(temp_project_dir) / 'data' / 'raw' / 'defect_dataset_2022.csv'
        assert dataset_path.exists()
    finally:
        mod.get_project_root = original_get_root

def test_t011a_valid_data(temp_project_dir, mock_pristine_file, monkeypatch):
    """Test T011a with a valid defect dataset."""
    import code_01_data_acquisition as mod
    original_get_root = mod.get_project_root
    mod.get_project_root = lambda: Path(temp_project_dir)
    
    # Create a valid defect dataset
    dataset_path = Path(temp_project_dir) / 'data' / 'raw' / 'defect_dataset_2022.csv'
    with open(dataset_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['defect_type', 'defect_density', 'conductivity', 'elastic_tensor', 'fracture_energy'])
        writer.writeheader()
        writer.writerow({
            'defect_type': 'vacancy',
            'defect_density': '0.01',
            'conductivity': '100.5',
            'elastic_tensor': '[[1,0,0],[0,1,0],[0,0,1]]',
            'fracture_energy': '5.0'
        })
    
    try:
        result = step_2a_download_and_validate_defect_dataset()
        
        assert result['valid'] == True
        assert result['exclusions'] == 0
        
        validation_path = Path(temp_project_dir) / 'data' / 'state' / 'source_validation.json'
        assert validation_path.exists()
        
        with open(validation_path, 'r') as f:
            saved_data = json.load(f)
            assert saved_data['valid'] == True
    finally:
        mod.get_project_root = original_get_root

def test_t011a_missing_columns(temp_project_dir, mock_pristine_file, monkeypatch):
    """Test T011a when the defect dataset is missing required columns."""
    import code_01_data_acquisition as mod
    original_get_root = mod.get_project_root
    mod.get_project_root = lambda: Path(temp_project_dir)
    
    # Create a dataset with missing columns
    dataset_path = Path(temp_project_dir) / 'data' / 'raw' / 'defect_dataset_2022.csv'
    with open(dataset_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['defect_type', 'defect_density']) # Missing others
        writer.writeheader()
        writer.writerow({'defect_type': 'vacancy', 'defect_density': '0.01'})
    
    try:
        result = step_2a_download_and_validate_defect_dataset()
        
        assert result['valid'] == False
        assert 'Missing required columns' in result['reason']
    finally:
        mod.get_project_root = original_get_root

def test_t011a_empty_file(temp_project_dir, mock_pristine_file, monkeypatch):
    """Test T011a when the defect dataset file exists but is empty."""
    import code_01_data_acquisition as mod
    original_get_root = mod.get_project_root
    mod.get_project_root = lambda: Path(temp_project_dir)
    
    # Create an empty file
    dataset_path = Path(temp_project_dir) / 'data' / 'raw' / 'defect_dataset_2022.csv'
    with open(dataset_path, 'w') as f:
        pass # Empty file
    
    try:
        result = step_2a_download_and_validate_defect_dataset()
        
        assert result['valid'] == False
        assert 'empty' in result['reason'].lower()
    finally:
        mod.get_project_root = original_get_root
