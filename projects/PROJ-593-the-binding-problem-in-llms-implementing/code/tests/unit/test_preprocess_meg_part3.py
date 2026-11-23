"""
Unit tests for T008: Validate and store pre-processed MEG data.

Tests the validation logic and storage functionality of the MEG preprocessing pipeline.
"""

import os
import tempfile
import json
from pathlib import Path
import numpy as np
import pytest
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocess_meg import validate_psd_data, load_config


class TestValidatePSDData:
    """Tests for the validate_psd_data function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = load_config()
        self.n_channels = 10
        self.n_freqs = 129  # Typical for welch with nperseg=256
        
    def test_valid_psd_data(self):
        """Test validation passes for correctly normalized PSD data."""
        # Create valid normalized PSD data (unit area)
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        # Normalize to unit area
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        assert report['valid'] is True
        assert report['checks']['shape']['passed'] is True
        assert report['checks']['unit_area']['passed'] is True
        assert report['checks']['non_negative']['passed'] is True
        assert report['checks']['frequency_range']['passed'] is True
        assert report['checks']['no_nan_inf']['passed'] is True
    
    def test_invalid_shape(self):
        """Test validation fails for incorrect shape."""
        # Create PSD with wrong number of channels
        psd_array = np.random.rand(self.n_channels + 5, self.n_freqs)
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        assert report['valid'] is False
        assert report['checks']['shape']['passed'] is False
    
    def test_non_unit_area(self):
        """Test validation fails for non-unit area normalization."""
        # Create PSD not normalized to unit area
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        # Multiply by 2 to break unit area constraint
        psd_array = psd_array * 2
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        psd_array = psd_array * 2  # Now sum is 2, not 1
        
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        assert report['valid'] is False
        assert report['checks']['unit_area']['passed'] is False
    
    def test_negative_values(self):
        """Test validation fails for negative PSD values."""
        # Create PSD with negative values
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        psd_array[0, 0] = -0.5  # Introduce negative value
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        assert report['valid'] is False
        assert report['checks']['non_negative']['passed'] is False
    
    def test_nan_values(self):
        """Test validation fails for NaN values."""
        # Create PSD with NaN values
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        psd_array[0, 0] = np.nan
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        assert report['valid'] is False
        assert report['checks']['no_nan_inf']['passed'] is False
    
    def test_inf_values(self):
        """Test validation fails for Inf values."""
        # Create PSD with Inf values
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        psd_array[0, 0] = np.inf
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        assert report['valid'] is False
        assert report['checks']['no_nan_inf']['passed'] is False
    
    def test_wrong_frequency_range(self):
        """Test validation fails for incorrect frequency range."""
        # Create valid PSD
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        # Create frequency array outside expected range
        freqs = np.linspace(10, 20, self.n_freqs)  # Wrong range
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        # Note: The current implementation checks if freqs are within bounds
        # This test verifies the frequency range check works
        assert report['checks']['frequency_range']['passed'] is False
    
    def test_validation_report_structure(self):
        """Test that validation report has correct structure."""
        psd_array = np.random.rand(self.n_channels, self.n_freqs)
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        freqs = np.linspace(30, 50, self.n_freqs)
        
        report = validate_psd_data(psd_array, freqs, self.config)
        
        # Check required keys exist
        assert 'valid' in report
        assert 'checks' in report
        assert isinstance(report['valid'], bool)
        assert isinstance(report['checks'], dict)
        
        # Check all expected checks are present
        expected_checks = ['shape', 'unit_area', 'non_negative', 'frequency_range', 'no_nan_inf']
        for check in expected_checks:
            assert check in report['checks']
            assert 'passed' in report['checks'][check]


class TestPreprocessMegScriptExecution:
    """Tests for the main script execution and file storage."""
    
    def test_config_loading(self):
        """Test that configuration loads correctly."""
        config = load_config()
        
        assert 'meg' in config
        assert 'raw_path' in config['meg']
        assert 'filtered_path' in config['meg']
        assert 'psd_path' in config['meg']
        assert 'sampling_rate' in config['meg']
        assert 'lowcut' in config['meg']
        assert 'highcut' in config['meg']
        
        # Verify default values
        assert config['meg']['sampling_rate'] == 1000
        assert config['meg']['lowcut'] == 30
        assert config['meg']['highcut'] == 50
    
    def test_validation_report_creation(self):
        """Test that validation report is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock data
            n_channels = 5
            n_freqs = 50
            psd_array = np.random.rand(n_channels, n_freqs)
            psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
            freqs = np.linspace(30, 50, n_freqs)
            
            config = load_config()
            config['meg']['n_channels'] = n_channels
            
            report = validate_psd_data(psd_array, freqs, config)
            
            # Verify report structure
            assert 'valid' in report
            assert isinstance(report['valid'], bool)
            assert 'checks' in report
            assert isinstance(report['checks'], dict)
            
            # Verify all checks have 'passed' key
            for check_name, check_data in report['checks'].items():
                assert 'passed' in check_data
                assert isinstance(check_data['passed'], bool)
    
    def test_storage_path_construction(self):
        """Test that storage paths are constructed correctly."""
        config = load_config()
        
        raw_path = config['meg']['raw_path']
        filtered_path = config['meg']['filtered_path']
        psd_path = config['meg']['psd_path']
        
        # Verify paths are relative and under data/
        assert raw_path.startswith('data/')
        assert filtered_path.startswith('data/processed/')
        assert psd_path.startswith('data/processed/')
        
        # Verify file extensions
        assert raw_path.endswith('.parquet')
        assert filtered_path.endswith('.npy')
        assert psd_path.endswith('.npy')
    
    def test_validation_with_realistic_data(self):
        """Test validation with data resembling real MEG preprocessing output."""
        # Simulate realistic PSD data:
        # - 306 MEG channels (typical for MEG systems)
        # - Frequency resolution from Welch with nperseg=256
        n_channels = 306
        n_freqs = 129  # (256/2) + 1
        
        # Generate realistic PSD: higher power at lower frequencies, decaying
        freqs = np.linspace(30, 50, n_freqs)
        psd_array = np.zeros((n_channels, n_freqs))
        
        for ch in range(n_channels):
            # Simulate 1/f-like spectrum in gamma band
            psd_array[ch, :] = 1.0 / (freqs ** 1.5)
            # Add some noise
            psd_array[ch, :] += np.random.rand(n_freqs) * 0.01
        
        # Normalize to unit area
        psd_array = psd_array / psd_array.sum(axis=1, keepdims=True)
        
        config = load_config()
        config['meg']['n_channels'] = n_channels
        
        report = validate_psd_data(psd_array, freqs, config)
        
        # Should pass all checks
        assert report['valid'] is True
        assert report['checks']['shape']['passed'] is True
        assert report['checks']['unit_area']['passed'] is True
        assert report['checks']['non_negative']['passed'] is True
        assert report['checks']['frequency_range']['passed'] is True
        assert report['checks']['no_nan_inf']['passed'] is True
    
    def test_validation_failure_cases(self):
        """Test various failure cases in validation."""
        n_channels = 10
        n_freqs = 50
        freqs = np.linspace(30, 50, n_freqs)
        
        config = load_config()
        config['meg']['n_channels'] = n_channels
        
        # Case 1: Wrong shape
        psd_wrong_shape = np.random.rand(n_channels + 5, n_freqs)
        psd_wrong_shape = psd_wrong_shape / psd_wrong_shape.sum(axis=1, keepdims=True)
        report = validate_psd_data(psd_wrong_shape, freqs, config)
        assert report['valid'] is False
        assert report['checks']['shape']['passed'] is False
        
        # Case 2: Non-unit area
        psd_bad_area = np.random.rand(n_channels, n_freqs)
        psd_bad_area = psd_bad_area * 2  # Scale to break unit area
        psd_bad_area = psd_bad_area / psd_bad_area.sum(axis=1, keepdims=True)
        psd_bad_area = psd_bad_area * 2
        report = validate_psd_data(psd_bad_area, freqs, config)
        assert report['valid'] is False
        assert report['checks']['unit_area']['passed'] is False
        
        # Case 3: Negative values
        psd_negative = np.random.rand(n_channels, n_freqs)
        psd_negative[0, 0] = -1.0
        psd_negative = psd_negative / psd_negative.sum(axis=1, keepdims=True)
        report = validate_psd_data(psd_negative, freqs, config)
        assert report['valid'] is False
        assert report['checks']['non_negative']['passed'] is False