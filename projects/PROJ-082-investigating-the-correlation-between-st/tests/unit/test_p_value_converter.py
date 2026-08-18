"""
Unit tests for p_value_converter.py edge cases.

Tests cover:
- Conversion of valid p-values to effect sizes (r).
- Handling of p-values at boundaries (0, 1).
- Handling of invalid p-values (negative, > 1).
- Verification of the Fisher's Z to r transformation logic.
- Logging behavior for conversions.
"""
import pytest
import math
import logging
from pathlib import Path
import sys
import io
import csv

# Add project root to path for imports if running standalone
# In the actual pipeline, this is handled by the runner
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.extraction.p_value_converter import (
    p_to_z_two_tailed,
    convert_p_value_to_effect_size,
    log_conversion
)
from utils.logger import get_logger


class TestPToZTwoTailed:
    """Tests for the p_to_z_two_tailed function."""

    def test_p_value_05(self):
        """Standard p=0.05 should yield a specific Z value."""
        # Two-tailed p=0.05 corresponds to Z ≈ 1.95996
        z = p_to_z_two_tailed(0.05)
        assert abs(z - 1.959963984540054) < 1e-6

    def test_p_value_01(self):
        """Standard p=0.01 should yield a specific Z value."""
        # Two-tailed p=0.01 corresponds to Z ≈ 2.57583
        z = p_to_z_two_tailed(0.01)
        assert abs(z - 2.5758293035489004) < 1e-6

    def test_p_value_near_zero(self):
        """P-values very close to 0 should yield large Z."""
        z = p_to_z_two_tailed(1e-10)
        assert z > 6.0

    def test_p_value_near_one(self):
        """P-values very close to 1 should yield Z near 0."""
        z = p_to_z_two_tailed(0.9999)
        assert abs(z) < 0.001

    def test_p_value_zero_raises(self):
        """P-value of exactly 0 should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_z_two_tailed(0.0)

    def test_p_value_one_raises(self):
        """P-value of exactly 1 should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_z_two_tailed(1.0)

    def test_p_value_negative_raises(self):
        """Negative p-value should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_z_two_tailed(-0.1)

    def test_p_value_greater_than_one_raises(self):
        """P-value > 1 should raise ValueError."""
        with pytest.raises(ValueError):
            p_to_z_two_tailed(1.5)


class TestConvertPValueToEffectSize:
    """Tests for the convert_p_value_to_effect_size function."""

    def test_valid_conversion(self):
        """Test a valid conversion with N provided."""
        p = 0.05
        n = 100
        r, z = convert_p_value_to_effect_size(p, n)
        # Check that r is within valid bounds [-1, 1]
        assert -1.0 <= r <= 1.0
        # Check that r corresponds to the Z score (approx 1.96 for p=0.05)
        # r = Z / sqrt(Z^2 + N - 2)
        expected_r = 1.95996 / math.sqrt(1.95996**2 + 100 - 2)
        assert abs(r - expected_r) < 0.01

    def test_small_sample_size(self):
        """Test conversion with small N."""
        p = 0.05
        n = 10
        r, z = convert_p_value_to_effect_size(p, n)
        assert -1.0 <= r <= 1.0

    def test_large_sample_size(self):
        """Test conversion with large N."""
        p = 0.05
        n = 10000
        r, z = convert_p_value_to_effect_size(p, n)
        assert -1.0 <= r <= 1.0
        # With large N, r should be very small for p=0.05
        assert abs(r) < 0.1

    def test_missing_n_returns_none(self):
        """If N is missing, function should return (None, None)."""
        p = 0.05
        r, z = convert_p_value_to_effect_size(p, None)
        assert r is None
        assert z is None

    def test_invalid_p_value_handling(self):
        """Test behavior with invalid p-value (should raise or handle gracefully)."""
        # The function should raise ValueError for invalid p
        with pytest.raises(ValueError):
            convert_p_value_to_effect_size(1.5, 100)

    def test_zero_studies_handling(self):
        """Test with N=0 (should handle gracefully or raise)."""
        # N=0 is mathematically invalid for this formula
        with pytest.raises((ValueError, ZeroDivisionError)):
            convert_p_value_to_effect_size(0.05, 0)


class TestLogConversion:
    """Tests for the logging functionality."""

    def test_log_conversion_creates_entry(self, caplog):
        """Verify that log_conversion writes to the logger."""
        caplog.set_level(logging.INFO)
        
        # Create a mock logger for testing
        logger = get_logger("test_p_value_converter")
        
        # Capture log output
        with caplog.at_level(logging.INFO):
            log_conversion(logger, 0.05, 100, 0.1, 1.96)
        
        # Check that a log entry was created
        assert any("0.05" in record.message for record in caplog.records)
        assert any("100" in record.message for record in caplog.records)

    def test_log_conversion_with_none_values(self, caplog):
        """Verify logging works when values are None."""
        caplog.set_level(logging.INFO)
        logger = get_logger("test_p_value_converter")
        
        with caplog.at_level(logging.INFO):
            log_conversion(logger, 0.05, None, None, None)
        
        assert any("0.05" in record.message for record in caplog.records)


class TestIntegration:
    """Integration-style tests for the module."""

    def test_full_pipeline_edge_case(self):
        """Test a full conversion pipeline with edge case data."""
        test_cases = [
            (0.05, 100, True),   # Valid
            (0.01, 50, True),    # Valid
            (0.5, 20, True),     # Valid, small effect
            (0.99, 100, True),   # Valid, very small effect
            (0.0, 100, False),   # Invalid p
            (1.0, 100, False),   # Invalid p
            (0.05, 0, False),    # Invalid N
        ]
        
        for p, n, should_succeed in test_cases:
            if should_succeed:
                r, z = convert_p_value_to_effect_size(p, n)
                assert r is not None
                assert z is not None
                assert -1.0 <= r <= 1.0
            else:
                with pytest.raises((ValueError, ZeroDivisionError)):
                    convert_p_value_to_effect_size(p, n)