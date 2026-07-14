"""
Unit tests for edge cases across the pipeline modules.
These tests validate robustness against boundary conditions and error states.
"""
import json
import os
import tempfile
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import from code modules (relative to project root when run via pytest)
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import init_reproducibility, get_config, update_config
from utils import verify_checksum, retry_download
from spectrum_computation import validate_sky_coverage
from inference import log_likelihood, prior_transform, check_convergence
from model_comparison import compute_bayes_factor, interpret_bayes_factor
from validation import split_sky_north_south


class TestConfigEdgeCases:
    def test_init_reproducibility_with_seed_zero(self):
        """Test reproducibility initialization with seed=0."""
        init_reproducibility(0)
        config = get_config()
        assert config['random_seed'] == 0
        assert 'numpy_seed' in config

    def test_init_reproducibility_with_negative_seed(self):
        """Test that negative seeds are handled or raise appropriate error."""
        # Depending on implementation, this might raise or wrap
        with pytest.raises((ValueError, TypeError)):
            init_reproducibility(-1)

    def test_update_config_with_empty_dict(self):
        """Test updating config with empty dictionary."""
        init_reproducibility(42)
        original = get_config()
        update_config({})
        assert get_config() == original


class TestUtilsEdgeCases:
    def test_verify_checksum_with_empty_file(self):
        """Test checksum verification on an empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'')
            temp_path = f.name
        try:
            # SHA256 of empty string
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert verify_checksum(temp_path, expected) is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_with_corrupted_file(self):
        """Test checksum verification fails on corrupted data."""
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as f:
            f.write(b'corrupted data')
            temp_path = f.name
        try:
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert verify_checksum(temp_path, expected) is False
        finally:
            os.unlink(temp_path)

    @patch('utils.requests.get')
    def test_retry_download_with_immediate_failure(self, mock_get):
        """Test retry logic when download fails immediately."""
        mock_get.side_effect = Exception("Network error")
        with pytest.raises(Exception):
            retry_download("http://example.com/data.fits", max_retries=2, base_delay=0.01)

    @patch('utils.requests.get')
    def test_retry_download_with_successful_retry(self, mock_get):
        """Test retry logic succeeds after one failure."""
        mock_get.side_effect = [
            Exception("First attempt failed"),
            MagicMock(content=b"success data")
        ]
        result = retry_download("http://example.com/data.fits", max_retries=3, base_delay=0.01)
        assert result == b"success data"


class TestSpectrumComputationEdgeCases:
    def test_validate_sky_coverage_exactly_70_percent(self):
        """Test validation passes at exactly 70% coverage."""
        # Mock healpy functions
        with patch('spectrum_computation.hp') as mock_hp:
            mock_hp.nside2npix.return_value = 100
            # Create a mask with exactly 70 non-zero pixels
            mask = np.zeros(100, dtype=int)
            mask[:70] = 1
            mock_hp.ma.return_value = mask
            
            result = validate_sky_coverage(mask)
            assert result is True

    def test_validate_sky_coverage_below_70_percent(self):
        """Test validation fails below 70% coverage."""
        with patch('spectrum_computation.hp') as mock_hp:
            mock_hp.nside2npix.return_value = 100
            mask = np.zeros(100, dtype=int)
            mask[:69] = 1
            mock_hp.ma.return_value = mask
            
            with pytest.raises(ValueError, match="Sky coverage"):
                validate_sky_coverage(mask)

    def test_validate_sky_coverage_with_all_masked(self):
        """Test validation fails when all pixels are masked."""
        with patch('spectrum_computation.hp') as mock_hp:
            mock_hp.nside2npix.return_value = 100
            mask = np.zeros(100, dtype=int)
            mock_hp.ma.return_value = mask
            
            with pytest.raises(ValueError, match="Sky coverage"):
                validate_sky_coverage(mask)


class TestInferenceEdgeCases:
    def test_log_likelihood_with_nan_data(self):
        """Test log_likelihood handles NaN in data gracefully."""
        # Simulate data with NaN
        data = {'cl': np.array([1.0, np.nan, 3.0]), 'var': np.array([0.1, 0.1, 0.1])}
        params = {'r': 0.01}
        
        # Should not crash, but may return -inf or raise specific error
        result = log_likelihood(params, data)
        assert np.isfinite(result) is False or result == -np.inf

    def test_prior_transform_with_boundary_values(self):
        """Test prior_transform at exact boundaries."""
        # r in [0, 0.1], E_PT in [1e14, 1e16]
        u = [0.0, 0.0]  # Lower bounds
        result = prior_transform(u)
        assert result['r'] == 0.0
        assert result['E_PT'] == 1e14

        u = [1.0, 1.0]  # Upper bounds
        result = prior_transform(u)
        assert result['r'] == 0.1
        assert result['E_PT'] == 1e16

    def test_check_convergence_with_undefined_evidence(self):
        """Test convergence check when evidence is undefined."""
        sampler = MagicMock()
        sampler.results = {'logz': None, 'logzerr': None}
        
        result = check_convergence(sampler)
        assert result is False


class TestModelComparisonEdgeCases:
    def test_compute_bayes_factor_with_zero_evidence(self):
        """Test Bayes factor when one model has zero evidence."""
        logz1 = -100.0
        logz2 = -np.inf  # Zero evidence in linear scale
        
        with pytest.raises((ValueError, FloatingPointError)):
            compute_bayes_factor(logz1, logz2)

    def test_interpret_bayes_factor_at_thresholds(self):
        """Test interpretation at exact decision thresholds."""
        assert interpret_bayes_factor(10.0) == "Strong evidence"
        assert interpret_bayes_factor(100.0) == "Very strong evidence"

    def test_interpret_bayes_factor_below_threshold(self):
        """Test interpretation below decision threshold."""
        assert "insignificant" in interpret_bayes_factor(5.0).lower()


class TestValidationEdgeCases:
    def test_split_sky_north_south_with_empty_mask(self):
        """Test sky split with all-masked input."""
        with patch('validation.hp') as mock_hp:
            mock_hp.nside2npix.return_value = 100
            # All zeros (masked)
            mask = np.zeros(100, dtype=int)
            
            with pytest.raises(ValueError, match="No valid pixels"):
                split_sky_north_south(mask)

    def test_split_sky_north_south_with_uneven_split(self):
        """Test sky split when one hemisphere has very few pixels."""
        with patch('validation.hp') as mock_hp:
            mock_hp.nside2npix.return_value = 100
            # Only 5 pixels in north, 95 in south
            mask = np.zeros(100, dtype=int)
            mask[:5] = 1  # North
            mask[50:100] = 1  # South
            
            north_mask, south_mask = split_sky_north_south(mask)
            assert np.sum(north_mask) == 5
            assert np.sum(south_mask) == 50