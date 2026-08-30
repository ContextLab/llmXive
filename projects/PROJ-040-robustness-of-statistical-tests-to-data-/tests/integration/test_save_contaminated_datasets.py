import os
import sys
import yaml
import hashlib
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.save_contaminated_datasets import compute_sha256, save_derivation_log, process_and_save_contamination

@pytest.fixture
def processed_dir():
    return project_root / "data" / "processed"

def test_contaminated_files_exist(processed_dir):
    """Test that T013 produces the expected contaminated dataset files."""
    # Check for at least one contaminated file
    contaminated_files = list(processed_dir.glob("*contaminated*.csv"))
    assert len(contaminated_files) > 0, "No contaminated files found in data/processed/"

def test_derivation_logs_exist(processed_dir):
    """Test that T013 produces derivation logs for each contaminated file."""
    contaminated_files = list(processed_dir.glob("*contaminated*.csv"))
    for csv_file in contaminated_files:
        log_file = csv_file.with_suffix('.log.yaml')
        assert log_file.exists(), f"Derivation log missing for {csv_file.name}"

def test_log_content_structure(processed_dir):
    """Test that derivation logs contain required fields."""
    contaminated_files = list(processed_dir.glob("*contaminated*.csv"))
    if not contaminated_files:
        pytest.skip("No contaminated files to test logs against.")
    
    for csv_file in contaminated_files:
        log_file = csv_file.with_suffix('.log.yaml')
        with open(log_file, 'r') as f:
            log_data = yaml.safe_load(f)
        
        required_fields = ['timestamp', 'source_file', 'source_hash', 'seed_used', 
                           'contamination_parameters', 'output_checksum', 'derivation_type']
        
        for field in required_fields:
            assert field in log_data, f"Missing field '{field}' in log for {csv_file.name}"

def test_checksum_matches_file(processed_dir):
    """Test that the checksum in the log matches the actual file hash."""
    contaminated_files = list(processed_dir.glob("*contaminated*.csv"))
    if not contaminated_files:
        pytest.skip("No contaminated files to test checksums.")
    
    for csv_file in contaminated_files:
        log_file = csv_file.with_suffix('.log.yaml')
        with open(log_file, 'r') as f:
            log_data = yaml.safe_load(f)
        
        expected_checksum = log_data['output_checksum']
        actual_checksum = compute_sha256(str(csv_file))
        
        assert expected_checksum == actual_checksum, \
            f"Checksum mismatch for {csv_file.name}: Expected {expected_checksum}, Got {actual_checksum}"

def test_data_integrity(processed_dir):
    """Test that the contaminated CSV files are valid and readable."""
    contaminated_files = list(processed_dir.glob("*contaminated*.csv"))
    if not contaminated_files:
        pytest.skip("No contaminated files to test integrity.")
    
    for csv_file in contaminated_files:
        try:
            df = pd.read_csv(csv_file)
            assert df.shape[0] > 0, f"File {csv_file.name} is empty."
            assert df.shape[1] > 0, f"File {csv_file.name} has no columns."
        except Exception as e:
            pytest.fail(f"Failed to read {csv_file.name}: {e}")
