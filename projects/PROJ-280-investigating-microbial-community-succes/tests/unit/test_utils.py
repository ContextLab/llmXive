"""
Unit tests for code/utils.py utility functions.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the functions to test
from utils import (
    benjamini_hochberg_fdr,
    calculate_permanova_power,
    calculate_vif,
    generate_checksum,
    log_data_gap_flag,
    log_under_determined_flag,
    log_underpowered_flag,
    validate_power_requirements,
)


class TestVIF:
    """Tests for Variance Inflation Factor calculation."""

    def test_vif_perfect_collinearity(self):
        """Test VIF when there is perfect collinearity."""
        # Create DataFrame with perfect collinearity
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],  # x2 = 2 * x1
        })

        vif = calculate_vif(df)

        # Both should be infinite due to perfect collinearity
        assert np.isinf(vif['x1']) or vif['x1'] > 100
        assert np.isinf(vif['x2']) or vif['x2'] > 100

    def test_vif_no_collinearity(self):
        """Test VIF when there is no collinearity."""
        # Create DataFrame with independent variables
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100),
        })

        vif = calculate_vif(df)

        # VIF should be close to 1 for independent variables
        assert all(vif < 2), "VIF values should be low for independent variables"

    def test_vif_empty_dataframe(self):
        """Test VIF with empty DataFrame."""
        df = pd.DataFrame()
        with pytest.raises(ValueError):
            calculate_vif(df)

    def test_vif_non_numeric(self):
        """Test VIF with non-numeric data."""
        df = pd.DataFrame({
            'x1': ['a', 'b', 'c'],
            'x2': [1, 2, 3],
        })
        with pytest.raises(ValueError):
            calculate_vif(df)


class TestBenjaminiHochberg:
    """Tests for Benjamini-Hochberg FDR correction."""

    def test_bh_basic(self):
        """Test basic BH correction."""
        p_values = [0.01, 0.04, 0.03, 0.001, 0.06]
        adjusted, rejected = benjamini_hochberg_fdr(p_values)

        assert len(adjusted) == len(p_values)
        assert len(rejected) == len(p_values)
        assert all(0 <= p <= 1 for p in adjusted)

    def test_bh_all_significant(self):
        """Test when all p-values are significant after correction."""
        p_values = [0.001, 0.002, 0.003, 0.004, 0.005]
        adjusted, rejected = benjamini_hochberg_fdr(p_values)

        # At least some should be rejected
        assert sum(rejected) > 0

    def test_bh_none_significant(self):
        """Test when no p-values are significant after correction."""
        p_values = [0.5, 0.6, 0.7, 0.8, 0.9]
        adjusted, rejected = benjamini_hochberg_fdr(p_values)

        # None should be rejected
        assert sum(rejected) == 0

    def test_bh_empty_list(self):
        """Test with empty p-values list."""
        with pytest.raises(ValueError):
            benjamini_hochberg_fdr([])

    def test_bh_invalid_pvalues(self):
        """Test with invalid p-values (outside [0, 1])."""
        with pytest.raises(ValueError):
            benjamini_hochberg_fdr([0.5, -0.1, 1.5])


class TestChecksum:
    """Tests for checksum generation."""

    def test_checksum_consistency(self):
        """Test that checksum is consistent for same file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum1 = generate_checksum(temp_path)
            checksum2 = generate_checksum(temp_path)
            assert checksum1 == checksum2
        finally:
            os.unlink(temp_path)

    def test_checksum_content_change(self):
        """Test that checksum changes when content changes."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            checksum1 = generate_checksum(temp_path)

            # Modify file
            with open(temp_path, 'w') as f:
                f.write("different content")

            checksum2 = generate_checksum(temp_path)
            assert checksum1 != checksum2
        finally:
            os.unlink(temp_path)

    def test_checksum_nonexistent_file(self):
        """Test checksum for non-existent file."""
        with pytest.raises(FileNotFoundError):
            generate_checksum("/nonexistent/path/file.txt")


class TestPowerAnalysis:
    """Tests for power analysis functions."""

    def test_calculate_permanova_power_basic(self):
        """Test basic power calculation."""
        result = calculate_permanova_power(n_groups=3, n_per_group=30)

        assert 'power' in result
        assert 'n_per_group' in result
        assert 'effect_size' in result
        assert 'flag' in result
        assert result['flag'] in ['PASS', 'UNDERPOWERED']
        assert 0 <= result['power'] <= 1

    def test_calculate_permanova_power_high_sample(self):
        """Test power calculation with high sample size."""
        result = calculate_permanova_power(n_groups=3, n_per_group=100)

        # Higher sample size should give higher power
        assert result['power'] >= 0.8
        assert result['flag'] == 'PASS'

    def test_calculate_permanova_power_low_sample(self):
        """Test power calculation with low sample size."""
        result = calculate_permanova_power(n_groups=3, n_per_group=5)

        # Low sample size should give lower power
        assert result['power'] < 0.8
        assert result['flag'] == 'UNDERPOWERED'

    def test_validate_power_requirements(self):
        """Test power requirements validation."""
        result = validate_power_requirements(n_samples=150, n_groups=3)

        assert 'current_n_samples' in result
        assert 'power_analysis' in result
        assert 'recommendation' in result
        assert isinstance(result['recommendation'], str)


class TestLoggingFlags:
    """Tests for logging flag functions."""

    def test_log_data_gap_flag(self, caplog):
        """Test DATA GAP flag logging."""
        log_data_gap_flag("Test data gap message")
        # Should log at CRITICAL level
        assert "CRITICAL DATA GAP" in caplog.text

    def test_log_underpowered_flag(self, caplog):
        """Test UNDERPOWERED flag logging."""
        log_underpowered_flag("Test underpowered message")
        assert "UNDERPOWERED" in caplog.text

    def test_log_under_determined_flag(self, caplog):
        """Test UNDER-DETERMINED flag logging."""
        log_under_determined_flag("Test under-determined message")
        assert "UNDER-DETERMINED" in caplog.text