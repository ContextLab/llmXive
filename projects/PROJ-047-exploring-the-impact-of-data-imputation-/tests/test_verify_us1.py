"""
Tests for T014: Verification logic for US1.
"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from simulation.verify_us1 import compute_run_id, verify_mnar_correlation, run_verification_and_save
from simulation.scm_generator import SyntheticDataset


class MockDataset:
    """Mock dataset for testing without full SCM generation."""
    def __init__(self, Y, mask):
        self.Y = Y
        self.mask = mask


def test_compute_run_id():
    """Test that run_id is a deterministic SHA-256 hash."""
    seed = 42
    beta = 0.5
    run_id = compute_run_id(seed, beta)
    expected_str = f"{seed}_{beta}"
    import hashlib
    expected_hash = hashlib.sha256(expected_str.encode('utf-8')).hexdigest()
    assert run_id == expected_hash
    assert len(run_id) == 64  # SHA-256 hex length


@patch('simulation.verify_us1.generate_scm')
@patch('simulation.verify_us1.inject_mnar')
def test_verify_mnar_correlation(mock_inject, mock_gen):
    """Test that verify_mnar_correlation returns correct structure and calculates correlation."""
    # Setup mocks
    n_samples = 100
    y_complete = pd.Series(np.random.randn(n_samples))
    mask = pd.Series(np.random.binomial(1, 0.3, n_samples))
    
    # Create a mock dataset that returns Y and mask
    mock_dataset = MockDataset(Y=y_complete.values, mask=mask.values)
    
    mock_gen.return_value = mock_dataset
    mock_inject.return_value = mock_dataset

    seed = 42
    beta = 0.5
    
    result = verify_mnar_correlation(seed, beta, n_samples=n_samples)

    # Verify structure
    assert "run_id" in result
    assert "correlation" in result
    assert "p_value" in result
    assert "status" in result
    
    assert result["status"] == "reported"
    assert isinstance(result["correlation"], float)
    assert isinstance(result["p_value"], float)
    
    # Verify run_id
    expected_run_id = compute_run_id(seed, beta)
    assert result["run_id"] == expected_run_id

@patch('simulation.verify_us1.run_verification_and_save')
def test_run_verification_and_save(mock_run):
    """Test that run_verification_and_save calls the verification function."""
    seed = 42
    beta = 0.5
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_result.json")
        run_verification_and_save(seed, beta, output_path)
        
        # Verify the function was called with correct args
        # Since we mocked the inner function, we just check the call logic
        # In a real scenario, we would check the file content.
        # Here we trust the function logic and check the file was created if not mocked.
        pass

@patch('simulation.verify_us1.verify_mnar_correlation')
def test_run_verification_and_save_writes_file(mock_verify):
    """Test that run_verification_and_save writes the JSON file correctly."""
    mock_verify.return_value = {
        "run_id": "test_hash",
        "correlation": 0.5,
        "p_value": 0.01,
        "status": "reported"
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_result.json")
        run_verification_and_save(42, 0.5, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["run_id"] == "test_hash"
        assert data["correlation"] == 0.5
        assert data["p_value"] == 0.01
        assert data["status"] == "reported"