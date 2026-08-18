"""
Unit tests for T012c: generate_synthetic_proxy.py
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path to import the script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.ingestion.generate_synthetic_proxy import (
    check_fetch_status,
    generate_synthetic_weights,
    STATUS_FILE,
    OUTPUT_PATH,
    HIDDEN_SIZE,
    RANK,
    NUM_LAYERS
)

class TestGenerateSyntheticProxy:
    def test_check_fetch_status_success(self, tmp_path):
        """Test that check_fetch_status returns 'success' when file indicates success."""
        status_file = tmp_path / "data_fetch_status.json"
        status_file.parent.mkdir(parents=True)
        with open(status_file, 'w') as f:
            json.dump({"status": "success"}, f)
        
        with patch('src.ingestion.generate_synthetic_proxy.STATUS_FILE', str(status_file)):
            result = check_fetch_status()
            assert result == "success"

    def test_check_fetch_status_failed(self, tmp_path):
        """Test that check_fetch_status returns 'failed' when file indicates failure."""
        status_file = tmp_path / "data_fetch_status.json"
        status_file.parent.mkdir(parents=True)
        with open(status_file, 'w') as f:
            json.dump({"status": "failed"}, f)
        
        with patch('src.ingestion.generate_synthetic_proxy.STATUS_FILE', str(status_file)):
            result = check_fetch_status()
            assert result == "failed"

    def test_check_fetch_status_missing_file(self, tmp_path):
        """Test that check_fetch_status returns 'success' when file is missing."""
        non_existent = tmp_path / "does_not_exist.json"
        with patch('src.ingestion.generate_synthetic_proxy.STATUS_FILE', str(non_existent)):
            result = check_fetch_status()
            assert result == "success"

    def test_generate_synthetic_weights_structure(self, tmp_path):
        """Test that generated weights have the correct structure and dimensions."""
        output_file = tmp_path / "test_proxy.npz"
        
        # Patch constants to use temp directory
        with patch('src.ingestion.generate_synthetic_proxy.OUTPUT_PATH', str(output_file)):
            generate_synthetic_weights()
        
        assert output_file.exists(), "Output file was not created."
        
        data = np.load(str(output_file))
        
        # Verify number of arrays
        # NUM_LAYERS * 4 projections * 2 matrices (A, B)
        expected_count = NUM_LAYERS * 4 * 2
        assert len(data.files) == expected_count, f"Expected {expected_count} arrays, got {len(data.files)}"
        
        # Verify dimensions of one array (A matrix)
        # A matrix: (rank, hidden_size) -> flattened size = rank * hidden_size
        expected_dim = RANK * HIDDEN_SIZE
        
        # Pick the first key
        first_key = data.files[0]
        arr = data[first_key]
        
        assert arr.shape == (expected_dim,), f"Array {first_key} has shape {arr.shape}, expected ({expected_dim},)"
        assert arr.dtype == np.float32, f"Array {first_key} has dtype {arr.dtype}, expected float32"

    def test_generate_synthetic_weights_seed_reproducibility(self, tmp_path):
        """Test that generation is reproducible with the same seed."""
        output_file_1 = tmp_path / "proxy1.npz"
        output_file_2 = tmp_path / "proxy2.npz"
        
        # First run
        with patch('src.ingestion.generate_synthetic_proxy.OUTPUT_PATH', str(output_file_1)):
            generate_synthetic_weights()
        
        # Second run
        with patch('src.ingestion.generate_synthetic_proxy.OUTPUT_PATH', str(output_file_2)):
            generate_synthetic_weights()
        
        data1 = np.load(str(output_file_1))
        data2 = np.load(str(output_file_2))
        
        # Check that all arrays are identical
        for key in data1.files:
            assert np.array_equal(data1[key], data2[key]), f"Data mismatch for {key}"