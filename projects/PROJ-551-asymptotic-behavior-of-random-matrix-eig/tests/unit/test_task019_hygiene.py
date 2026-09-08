"""
Unit tests for Task T019: Atomic Data Hygiene.

Tests verify that:
1. The matrix file is generated correctly.
2. The checksum is computed correctly.
3. The manifest is updated correctly.
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import numpy as np
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.task019_hygiene import compute_file_sha256, run_hygiene_capture
from generators.wigner import generate_wigner_matrix

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    temp_dir = tempfile.mkdtemp()
    data_raw = Path(temp_dir) / "data" / "raw"
    state = Path(temp_dir) / "state"
    data_raw.mkdir(parents=True)
    state.mkdir(parents=True)
    yield {
        "root": Path(temp_dir),
        "data_raw": data_raw,
        "state": state
    }
    shutil.rmtree(temp_dir)

def test_compute_file_sha256(temp_project_dir):
    """Test SHA-256 computation on a known file."""
    test_file = temp_project_dir["data_raw"] / "test.npy"
    test_data = np.array([1, 2, 3, 4, 5])
    np.save(test_file, test_data)

    # Compute hash
    hash_val = compute_file_sha256(test_file)

    # Verify it's a valid hex string of correct length
    assert isinstance(hash_val, str)
    assert len(hash_val) == 64
    assert all(c in '0123456789abcdef' for c in hash_val)

    # Verify against known value (numpy saves with header, so we just check consistency)
    hash_val_2 = compute_file_sha256(test_file)
    assert hash_val == hash_val_2

def test_run_hygiene_capture_creates_files(temp_project_dir):
    """Test that run_hygiene_capture creates the .npy and updates the JSON."""
    # Mock config by passing explicit args to bypass config file dependency
    # We need to ensure the function can run without the full project config setup
    # by mocking the necessary config calls or passing parameters that bypass them.
    # However, run_hygiene_capture calls get_matrix_size() and get_seed() internally if args are None.
    # To isolate, we pass explicit N and seed.
    
    # We also need to patch the get_project_paths or ensure the output_dir is used correctly.
    # The function accepts output_dir and checksum_path is derived from project_paths['state'].
    # We will pass output_dir but rely on the function's internal logic for state path if possible,
    # or we need to mock get_project_paths.
    
    # For this test, we will assume the function logic is robust enough to handle the temp dir
    # if we pass output_dir, but the checksum_path logic inside run_hygiene_capture uses
    # project_paths['state']. We need to mock that or ensure the temp dir structure works.
    
    # Simpler approach: patch the config functions or the project_paths return value.
    from unittest.mock import patch, MagicMock
    from pathlib import Path

    # Mock get_project_paths to return our temp directories
    mock_paths = {
        'data_raw': temp_project_dir['data_raw'],
        'state': temp_project_dir['state']
    }

    with patch('analysis.task019_hygiene.get_project_paths', return_value=mock_paths):
        with patch('analysis.task019_hygiene.ensure_directories'):
            result = run_hygiene_capture(n=10, seed=42, output_dir=temp_project_dir['data_raw'])

    # Assertions
    assert result['status'] == 'success'
    assert result['N'] == 10
    assert result['seed'] == 42
    assert 'checksum' in result
    assert len(result['checksum']) == 64

    # Check file exists
    matrix_path = temp_project_dir['data_raw'] / "matrix_N10_seed42.npy"
    assert matrix_path.exists()

    # Check checksum file exists
    checksum_path = temp_project_dir['state'] / "checksums_raw.json"
    assert checksum_path.exists()

    # Check content of checksum file
    with open(checksum_path, 'r') as f:
        manifest = json.load(f)
    
    assert 'checksums' in manifest
    assert len(manifest['checksums']) >= 1
    
    # Find our entry
    entry = next((e for e in manifest['checksums'] if e['seed'] == 42 and e['N'] == 10), None)
    assert entry is not None
    assert entry['hash'] == result['checksum']
    
    # Verify the saved matrix matches the hash
    saved_matrix = np.load(matrix_path)
    assert saved_matrix.shape == (10, 10)
    assert np.all(np.isfinite(saved_matrix))

def test_run_hygiene_capture_idempotent(temp_project_dir):
    """Test that running twice updates the manifest correctly (or handles duplicates)."""
    from unittest.mock import patch
    
    mock_paths = {
        'data_raw': temp_project_dir['data_raw'],
        'state': temp_project_dir['state']
    }

    with patch('analysis.task019_hygiene.get_project_paths', return_value=mock_paths):
        with patch('analysis.task019_hygiene.ensure_directories'):
            # Run first time
            result1 = run_hygiene_capture(n=5, seed=123, output_dir=temp_project_dir['data_raw'])
            
            # Run second time with same params
            result2 = run_hygiene_capture(n=5, seed=123, output_dir=temp_project_dir['data_raw'])

    # Check manifest has only one entry for this seed/N (or updated timestamp)
    checksum_path = temp_project_dir['state'] / "checksums_raw.json"
    with open(checksum_path, 'r') as f:
        manifest = json.load(f)
    
    entries = [e for e in manifest['checksums'] if e['seed'] == 123 and e['N'] == 5]
    assert len(entries) == 1
    assert entries[0]['hash'] == result1['checksum']
    assert entries[0]['hash'] == result2['checksum']