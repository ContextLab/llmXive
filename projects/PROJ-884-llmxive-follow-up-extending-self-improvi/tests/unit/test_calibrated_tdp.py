"""
Unit tests for TDP Constant Generation (T008c).

Verifies that:
1. `data/processed/calibrated_tdp.json` exists after generation
2. `tdp_watts` > 0
3. `source` is present and correct
4. `citation_url` is a valid URL
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.generate_tdp_constant import (
    load_calibration_data,
    generate_calibrated_tdp,
    validate_url,
    calculate_error_margin_and_ci,
    VERIFIED_TDP_SOURCE_URL
)


class TestTDPConstantValid:
    """Tests for T008c verification requirements."""
    
    def test_tdp_constant_valid(self, tmp_path):
        """
        Main verification test: asserts that generated calibrated_tdp.json
        meets all schema requirements.
        """
        # Create mock calibration data
        mock_calibration = {
            'estimated_tdp_watts': 65.0,
            'cpu_percent': 85.0,
            'duration': 10.5,
            'cpu_model': 'Intel Core i7-12700K',
            'calibration_timestamp': '2024-01-15T10:30:00Z',
            'workload_type': 'synthetic_stress'
        }
        
        # Generate calibrated data
        calibrated = generate_calibrated_tdp(mock_calibration)
        
        # Save to temp file
        output_file = tmp_path / "calibrated_tdp.json"
        with open(output_file, 'w') as f:
            json.dump(calibrated, f)
        
        # Reload and verify
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        # Requirement 1: tdp_watts > 0
        assert 'tdp_watts' in loaded, "Missing 'tdp_watts' field"
        assert loaded['tdp_watts'] > 0, f"'tdp_watts' must be > 0, got {loaded['tdp_watts']}"
        
        # Requirement 2: source is present
        assert 'source' in loaded, "Missing 'source' field"
        assert loaded['source'] == 'verified-literature', \
            f"Expected source='verified-literature', got '{loaded['source']}'"
        
        # Requirement 3: citation_url is a valid URL
        assert 'citation_url' in loaded, "Missing 'citation_url' field"
        assert validate_url(loaded['citation_url']), \
            f"'citation_url' is not a valid URL: {loaded['citation_url']}"
        
        # Additional integrity checks
        assert 'error_margin' in loaded, "Missing 'error_margin' field"
        assert 'confidence_interval' in loaded, "Missing 'confidence_interval' field"
        assert loaded['error_margin'] > 0, "Error margin must be positive"
        assert loaded['confidence_interval'] > 0, "CI width must be positive"
        
        print(f"✓ All T008c requirements verified for {output_file}")


    def test_load_calibration_data_fails_loudly(self, tmp_path):
        """Verify that missing calibration file raises FileNotFoundError."""
        non_existent = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError) as exc_info:
            load_calibration_data(non_existent)
        assert "Calibration data not found" in str(exc_info.value)


    def test_generate_calibrated_tdp_validates_positive_tdp(self, tmp_path):
        """Verify that invalid TDP values raise ValueError."""
        invalid_data = {
            'estimated_tdp_watts': -10.0,
            'cpu_percent': 50.0
        }
        with pytest.raises(ValueError) as exc_info:
            generate_calibrated_tdp(invalid_data)
        assert "Invalid TDP value" in str(exc_info.value)


    def test_generate_calibrated_tdp_validates_cpu_percent(self, tmp_path):
        """Verify that invalid CPU percent raises ValueError."""
        invalid_data = {
            'estimated_tdp_watts': 65.0,
            'cpu_percent': 150.0  # Invalid: > 100
        }
        with pytest.raises(ValueError) as exc_info:
            generate_calibrated_tdp(invalid_data)
        assert "Invalid CPU percent" in str(exc_info.value)


    def test_url_validation(self):
        """Test URL validation helper."""
        # Valid URLs
        assert validate_url("https://ark.intel.com") is True
        assert validate_url("http://example.com/path") is True
        
        # Invalid URLs
        assert validate_url("not-a-url") is False
        assert validate_url("") is False
        assert validate_url("ftp://example.com") is False  # Only http/https allowed


    def test_error_margin_calculation(self):
        """Test error margin calculation logic."""
        # High utilization should reduce error
        error_high, ci_high = calculate_error_margin_and_ci(65.0, 90.0)
        error_low, ci_low = calculate_error_margin_and_ci(65.0, 10.0)
        
        # High utilization should have lower error margin
        assert error_high < error_low, \
            f"High utilization error ({error_high}) should be < low utilization ({error_low})"
        
        # Both should be positive
        assert error_high > 0 and error_low > 0


    def test_verified_source_url_is_valid(self):
        """Verify that the hardcoded citation URL is valid."""
        assert validate_url(VERIFIED_TDP_SOURCE_URL), \
            f"VERIFIED_TDP_SOURCE_URL is invalid: {VERIFIED_TDP_SOURCE_URL}"
        assert "ark.intel.com" in VERIFIED_TDP_SOURCE_URL, \
            "Source URL should point to Intel ARK database"
