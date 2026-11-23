"""
Unit tests for injection-recovery logic (FR-008).

This module tests the core functionality of the injection-recovery pipeline:
- Signal injection into synthetic data
- Parameter recovery within credible intervals
- Edge cases and error handling
"""
import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from injection_recovery import (
    inject_yukawa_signal,
    check_recovery,
    load_harmonized_data
)
from data.loaders import HarmonizedDataset

# Mock data for testing
@pytest.fixture
def mock_dataset():
    """Create a mock harmonized dataset for testing."""
    n_points = 100
    separation_m = np.linspace(1e-5, 1e-4, n_points)
    # Generate fake force data (Newtonian only)
    force_n = 1e-15 * np.ones(n_points)  # Placeholder
    # Identity covariance for simplicity
    covariance_matrix = np.eye(n_points) * 1e-30
    
    return HarmonizedDataset(
        separation_m=separation_m,
        force_n=force_n,
        covariance_matrix=covariance_matrix,
        metadata={'test': True}
    )

@pytest.fixture
def mock_dataset_json(tmp_path):
    """Create a temporary JSON file for loading tests."""
    dataset = HarmonizedDataset(
        separation_m=np.array([1e-5, 5e-5, 1e-4]),
        force_n=np.array([1e-15, 2e-15, 3e-15]),
        covariance_matrix=np.eye(3) * 1e-30,
        metadata={'test': True}
    )
    
    data_dict = {
        'separation_m': dataset.separation_m.tolist(),
        'force_n': dataset.force_n.tolist(),
        'covariance_matrix': dataset.covariance_matrix.tolist(),
        'metadata': dataset.metadata
    }
    
    json_path = tmp_path / "mock_dataset.json"
    with open(json_path, 'w') as f:
        json.dump(data_dict, f)
    
    return json_path

class TestInjectYukawaSignal:
    """Tests for the inject_yukawa_signal function."""

    def test_injection_adds_positive_force(self, mock_dataset):
        """Test that injection adds a positive force shift."""
        alpha_true = 100.0
        lambda_true = 5e-5
        
        injected = inject_yukawa_signal(
            mock_dataset, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true,
            seed=42
        )
        
        # The injected force should be different from original
        assert not np.array_equal(injected.force_n, mock_dataset.force_n)
        
        # Assuming Yukawa force is positive for these parameters
        force_diff = injected.force_n - mock_dataset.force_n
        assert np.all(force_diff >= 0), "Yukawa injection should add positive force"

    def test_injection_preserves_separation(self, mock_dataset):
        """Test that separation distances remain unchanged after injection."""
        alpha_true = 100.0
        lambda_true = 5e-5
        
        injected = inject_yukawa_signal(
            mock_dataset, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        np.testing.assert_array_equal(
            injected.separation_m, 
            mock_dataset.separation_m
        )

    def test_injection_preserves_covariance(self, mock_dataset):
        """Test that covariance matrix remains unchanged after injection."""
        alpha_true = 100.0
        lambda_true = 5e-5
        
        injected = inject_yukawa_signal(
            mock_dataset, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        np.testing.assert_array_equal(
            injected.covariance_matrix, 
            mock_dataset.covariance_matrix
        )

    def test_injection_updates_metadata(self, mock_dataset):
        """Test that injection metadata is correctly updated."""
        alpha_true = 100.0
        lambda_true = 5e-5
        
        injected = inject_yukawa_signal(
            mock_dataset, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        assert 'injected_alpha' in injected.metadata
        assert 'injected_lambda' in injected.metadata
        assert injected.metadata['injected_alpha'] == alpha_true
        assert injected.metadata['injected_lambda'] == lambda_true

class TestCheckRecovery:
    """Tests for the check_recovery function."""

    def test_recovery_within_ci(self):
        """Test successful recovery when true value is within CI."""
        inference_results = {
            'alpha_ci_95': np.array([80.0, 120.0]),
            'lambda_ci_95': np.array([4e-5, 6e-5]),
            'alpha_median': 100.0,
            'lambda_median': 5e-5
        }
        
        alpha_true = 100.0
        lambda_true = 5e-5
        
        recovery = check_recovery(
            inference_results, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        assert recovery['alpha_recovered'] is True
        assert recovery['lambda_recovered'] is True
        assert recovery['overall_recovery'] is True

    def test_recovery_outside_ci(self):
        """Test failed recovery when true value is outside CI."""
        inference_results = {
            'alpha_ci_95': np.array([80.0, 90.0]),
            'lambda_ci_95': np.array([4e-5, 4.5e-5]),
            'alpha_median': 85.0,
            'lambda_median': 4.25e-5
        }
        
        alpha_true = 100.0
        lambda_true = 5e-5
        
        recovery = check_recovery(
            inference_results, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        assert recovery['alpha_recovered'] is False
        assert recovery['lambda_recovered'] is False
        assert recovery['overall_recovery'] is False

    def test_partial_recovery(self):
        """Test partial recovery (one parameter in CI, one out)."""
        inference_results = {
            'alpha_ci_95': np.array([80.0, 120.0]),
            'lambda_ci_95': np.array([4e-5, 4.5e-5]),
            'alpha_median': 100.0,
            'lambda_median': 4.25e-5
        }
        
        alpha_true = 100.0
        lambda_true = 5e-5
        
        recovery = check_recovery(
            inference_results, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        assert recovery['alpha_recovered'] is True
        assert recovery['lambda_recovered'] is False
        assert recovery['overall_recovery'] is False

    def test_recovery_calculates_distances(self):
        """Test that recovery calculates distances correctly."""
        inference_results = {
            'alpha_ci_95': np.array([80.0, 120.0]),
            'lambda_ci_95': np.array([4e-5, 6e-5]),
            'alpha_median': 100.0,
            'lambda_median': 5e-5
        }
        
        alpha_true = 110.0
        lambda_true = 5.5e-5
        
        recovery = check_recovery(
            inference_results, 
            alpha_true=alpha_true, 
            lambda_true=lambda_true
        )
        
        assert recovery['alpha_distance'] == 10.0
        assert recovery['lambda_distance'] == 0.5e-5

class TestLoadHarmonizedData:
    """Tests for the load_harmonized_data function."""

    def test_load_from_json(self, mock_dataset_json):
        """Test loading dataset from JSON file."""
        dataset = load_harmonized_data(mock_dataset_json)
        
        assert isinstance(dataset, HarmonizedDataset)
        assert len(dataset.separation_m) == 3
        assert len(dataset.force_n) == 3
        assert dataset.covariance_matrix.shape == (3, 3)

    def test_load_missing_file(self, tmp_path):
        """Test that loading a missing file raises FileNotFoundError."""
        missing_path = tmp_path / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_harmonized_data(missing_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])