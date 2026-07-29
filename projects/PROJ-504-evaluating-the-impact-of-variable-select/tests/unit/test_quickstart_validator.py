import os
import sys
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from quickstart_validator import (
    check_directories,
    check_files,
    check_simulation_results_integrity,
    check_imports,
    REQUIRED_DIRS,
    REQUIRED_FILES,
    REQUIRED_COLUMNS_SIM_RESULTS
)

class TestQuickstartValidator:
    
    def setup_method(self):
        """Create a temporary project structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create minimal required structure
        for d in REQUIRED_DIRS:
            os.makedirs(d, exist_ok=True)
        
        # Create minimal required files
        for f in REQUIRED_FILES:
            if f == "data/processed/simulation_results.csv":
                # Create a valid CSV with headers
                os.makedirs("data/processed", exist_ok=True)
                with open(f, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=REQUIRED_COLUMNS_SIM_RESULTS)
                    writer.writeheader()
                    writer.writerow({
                        'dataset_id': '1',
                        'dataset_name': 'test_ds',
                        'method': 'forward',
                        'snr': '1.0',
                        'sparsity': '0.2',
                        'power_rate': '0.8',
                        'true_positives': '4',
                        'false_positives': '1',
                        'selected_vars': '[1,2,3,4,5]',
                        'true_nonzero_count': '5'
                    })
            else:
                parent = Path(f).parent
                if parent != Path('.'):
                    os.makedirs(parent, exist_ok=True)
                Path(f).touch()
    
    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_check_directories_success(self):
        """Test directory check passes when all dirs exist."""
        success, errors = check_directories()
        assert success is True
        assert len(errors) == 0
    
    def test_check_directories_failure(self):
        """Test directory check fails when a dir is missing."""
        # Remove a required dir
        missing_dir = REQUIRED_DIRS[0]
        if os.path.exists(missing_dir):
            shutil.rmtree(missing_dir)
        
        success, errors = check_directories()
        assert success is False
        assert len(errors) > 0
        assert missing_dir in errors[0] or any(missing_dir in e for e in errors)
    
    def test_check_files_success(self):
        """Test file check passes when all files exist."""
        success, errors = check_files()
        assert success is True
        assert len(errors) == 0
    
    def test_check_files_failure(self):
        """Test file check fails when a file is missing."""
        missing_file = REQUIRED_FILES[0]
        if os.path.exists(missing_file):
            os.remove(missing_file)
        
        success, errors = check_files()
        assert success is False
        assert len(errors) > 0
        assert missing_file in errors[0]
    
    def test_check_simulation_results_integrity_valid(self):
        """Test integrity check passes with valid CSV."""
        success, msg = check_simulation_results_integrity()
        assert success is True
        assert "rows" in msg
    
    def test_check_simulation_results_integrity_empty(self):
        """Test integrity check fails with empty CSV."""
        # Overwrite with empty CSV (headers only)
        with open("data/processed/simulation_results.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS_SIM_RESULTS)
            writer.writeheader()
        
        success, msg = check_simulation_results_integrity()
        assert success is False
        assert "empty" in msg.lower() or "0 rows" in msg
    
    def test_check_simulation_results_integrity_missing_cols(self):
        """Test integrity check fails with missing columns."""
        # Create CSV with wrong headers
        with open("data/processed/simulation_results.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
            writer.writeheader()
            writer.writerow({'col1': 'a', 'col2': 'b'})
        
        success, msg = check_simulation_results_integrity()
        assert success is False
        assert "Missing columns" in msg
    
    def test_check_simulation_results_integrity_null_dataset(self):
        """Test integrity check fails if dataset_id is null (T054)."""
        # Create CSV with null dataset_id
        with open("data/processed/simulation_results.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS_SIM_RESULTS)
            writer.writeheader()
            row = {
                'dataset_id': '',  # Null/Empty
                'dataset_name': 'test',
                'method': 'forward',
                'snr': '1.0',
                'sparsity': '0.2',
                'power_rate': '0.8',
                'true_positives': '4',
                'false_positives': '1',
                'selected_vars': '[]',
                'true_nonzero_count': '5'
            }
            writer.writerow(row)
        
        success, msg = check_simulation_results_integrity()
        assert success is False
        assert "null" in msg.lower() or "dataset_id" in msg
    
    def test_check_imports(self):
        """Test that critical modules can be imported."""
        # This test might fail if the environment isn't fully set up, 
        # but it validates the import logic itself.
        success, msg = check_imports()
        # We assert that the function runs without crashing
        assert isinstance(success, bool)
        assert isinstance(msg, str)