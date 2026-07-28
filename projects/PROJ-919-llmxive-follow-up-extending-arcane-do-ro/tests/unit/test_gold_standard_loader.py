import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.lib.gold_standard_loader import (
    load_gold_standard,
    compute_file_checksum,
    verify_and_record_checksum,
    get_gold_standard_for_calibration
)

@pytest.fixture
def temp_gold_standard_file():
    """Creates a temporary gold standard JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        data = [
            {
                "character": "TestChar",
                "scenario": "test_probe",
                "ground_truth_score": 4.0,
                "ground_truth_phase": "Coarse"
            }
        ]
        json.dump(data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_state_dir():
    """Creates a temporary directory for state files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup handled by caller or pytest tmp_path if used differently

def test_load_gold_standard_valid(temp_gold_standard_file):
    """Test loading a valid gold standard file."""
    # Temporarily override the path for the test
    with patch('src.lib.gold_standard_loader.GOLD_STANDARD_PATH', Path(temp_gold_standard_file)):
        data = load_gold_standard()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['character'] == 'TestChar'

def test_load_gold_standard_not_found():
    """Test that FileNotFoundError is raised if file is missing."""
    with patch('src.lib.gold_standard_loader.GOLD_STANDARD_PATH', Path('/nonexistent/path.json')):
        with pytest.raises(FileNotFoundError):
            load_gold_standard()

def test_compute_file_checksum(temp_gold_standard_file):
    """Test checksum computation."""
    checksum = compute_file_checksum(Path(temp_gold_standard_file))
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_verify_and_record_checksum(temp_gold_standard_file, temp_state_dir):
    """Test checksum verification and recording."""
    # Setup mock paths
    gold_path = Path(temp_gold_standard_file)
    checksum_path = Path(temp_state_dir) / ".checksums.json"
    
    with patch('src.lib.gold_standard_loader.GOLD_STANDARD_PATH', gold_path):
        with patch('src.lib.gold_standard_loader.CHECKSUM_FILE_PATH', checksum_path):
            # First run: no stored checksum
            checksum, is_valid = verify_and_record_checksum()
            assert is_valid
            assert checksum_path.exists()
            
            # Second run: stored checksum should match
            checksum2, is_valid2 = verify_and_record_checksum()
            assert checksum == checksum2
            assert is_valid2

def test_get_gold_standard_for_calibration_failure(temp_gold_standard_file):
    """Test that RuntimeError is raised on checksum mismatch simulation."""
    gold_path = Path(temp_gold_standard_file)
    checksum_path = Path(temp_gold_standard_file).parent / ".checksums.json"
    
    # Pre-populate a wrong checksum
    wrong_checksum = "0" * 64
    with open(checksum_path, 'w') as f:
        json.dump({"human_annotations.json": wrong_checksum}, f)
    
    with patch('src.lib.gold_standard_loader.GOLD_STANDARD_PATH', gold_path):
        with patch('src.lib.gold_standard_loader.CHECKSUM_FILE_PATH', checksum_path):
            with pytest.raises(RuntimeError, match="checksum verification failed"):
                get_gold_standard_for_calibration()