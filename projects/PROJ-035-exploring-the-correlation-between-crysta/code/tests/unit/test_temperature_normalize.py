"""
Unit tests for temperature normalization module.

Tests for Slack (1979) normalization implementation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from src.cleaning.temperature_normalize import (
    slack_normalization_factor,
    normalize_thermal_conductivity,
    is_within_reference_window,
    normalize_dataframe,
    apply_temperature_normalization,
    REFERENCE_TEMPERATURE_K,
    TEMPERATURE_TOLERANCE_K,
    MIN_VALID_TEMP_K,
    MAX_VALID_TEMP_K
)


class TestSlackNormalizationFactor:
    """Tests for slack_normalization_factor function."""

    def test_basic_normalization_factor(self):
        """Test basic normalization factor calculation."""
        # At reference temperature, factor should be 1.0
        factor = slack_normalization_factor(300.0, 300.0)
        assert np.isclose(factor, 1.0, atol=1e-6)

    def test_higher_temperature_factor(self):
        """Test normalization factor when measured temp > reference."""
        # Higher temperature should give factor > 1
        factor = slack_normalization_factor(400.0, 300.0)
        expected = (400.0 / 300.0) ** 1.0
        assert np.isclose(factor, expected, atol=1e-6)

    def test_lower_temperature_factor(self):
        """Test normalization factor when measured temp < reference."""
        # Lower temperature should give factor < 1
        factor = slack_normalization_factor(200.0, 300.0)
        expected = (200.0 / 300.0) ** 1.0
        assert np.isclose(factor, expected, atol=1e-6)

    def test_custom_exponent(self):
        """Test normalization with custom exponent."""
        factor = slack_normalization_factor(400.0, 300.0, exponent=1.5)
        expected = (400.0 / 300.0) ** 1.5
        assert np.isclose(factor, expected, atol=1e-6)

    def test_invalid_negative_temperature(self):
        """Test that negative temperature raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            slack_normalization_factor(-100.0, 300.0)

    def test_invalid_zero_temperature(self):
        """Test that zero temperature raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            slack_normalization_factor(0.0, 300.0)

    def test_invalid_too_low_temperature(self):
        """Test that temperature below MIN_VALID_TEMP_K raises ValueError."""
        with pytest.raises(ValueError, match="outside valid range"):
            slack_normalization_factor(40.0, 300.0)

    def test_invalid_too_high_temperature(self):
        """Test that temperature above MAX_VALID_TEMP_K raises ValueError."""
        with pytest.raises(ValueError, match="outside valid range"):
            slack_normalization_factor(1600.0, 300.0)

    def test_invalid_reference_temperature(self):
        """Test that invalid reference temperature raises ValueError."""
        with pytest.raises(ValueError, match="positive"):
            slack_normalization_factor(300.0, 0.0)


class TestNormalizeThermalConductivity:
    """Tests for normalize_thermal_conductivity function."""

    def test_basic_normalization(self):
        """Test basic thermal conductivity normalization."""
        kappa_meas = 10.0  # W/m·K
        temp_meas = 400.0  # K
        kappa_norm = normalize_thermal_conductivity(kappa_meas, temp_meas, 300.0)

        # κ_ref = κ_meas * (T_meas / T_ref)
        expected = 10.0 * (400.0 / 300.0)
        assert np.isclose(kappa_norm, expected, atol=1e-6)

    def test_at_reference_temperature(self):
        """Test normalization at reference temperature returns same value."""
        kappa_meas = 15.5
        temp_meas = 300.0
        kappa_norm = normalize_thermal_conductivity(kappa_meas, temp_meas, 300.0)
        assert np.isclose(kappa_norm, kappa_meas, atol=1e-6)

    def test_low_temperature_normalization(self):
        """Test normalization from lower temperature."""
        kappa_meas = 20.0
        temp_meas = 200.0
        kappa_norm = normalize_thermal_conductivity(kappa_meas, temp_meas, 300.0)

        # Should increase because we're normalizing up to higher temp
        expected = 20.0 * (200.0 / 300.0)
        assert np.isclose(kappa_norm, expected, atol=1e-6)

    def test_invalid_temperature_raises(self):
        """Test that invalid temperature raises ValueError."""
        with pytest.raises(ValueError):
            normalize_thermal_conductivity(10.0, 40.0, 300.0)


class TestIsWithinReferenceWindow:
    """Tests for is_within_reference_window function."""

    def test_within_window_center(self):
        """Test temperature at center of window."""
        assert is_within_reference_window(300.0) is True

    def test_within_window_upper_bound(self):
        """Test temperature at upper bound of window."""
        assert is_within_reference_window(310.0) is True

    def test_within_window_lower_bound(self):
        """Test temperature at lower bound of window."""
        assert is_within_reference_window(290.0) is True

    def test_outside_window_upper(self):
        """Test temperature above window."""
        assert is_within_reference_window(311.0) is False

    def test_outside_window_lower(self):
        """Test temperature below window."""
        assert is_within_reference_window(289.0) is False

    def test_custom_reference_and_tolerance(self):
        """Test with custom reference temperature and tolerance."""
        assert is_within_reference_window(350.0, reference_temp=350.0, tolerance=5.0) is True
        assert is_within_reference_window(356.0, reference_temp=350.0, tolerance=5.0) is False


class TestNormalizeDataFrame:
    """Tests for normalize_dataframe function."""

    def test_basic_dataframe_normalization(self):
        """Test basic DataFrame normalization."""
        df = pd.DataFrame({
            'thermal_conductivity': [10.0, 15.0, 20.0],
            'temperature': [300.0, 400.0, 200.0]
        })

        result_df, warnings = normalize_dataframe(df)

        assert 'thermal_conductivity_normalized' in result_df.columns
        assert 'temperature_window_flag' in result_df.columns

        # First row should be unchanged (at reference temp)
        assert np.isclose(result_df.iloc[0]['thermal_conductivity_normalized'], 10.0)

        # Second row: 15 * (400/300) = 20
        assert np.isclose(result_df.iloc[1]['thermal_conductivity_normalized'], 20.0)

        # Third row: 20 * (200/300) = 13.33...
        expected = 20.0 * (200.0 / 300.0)
        assert np.isclose(result_df.iloc[2]['thermal_conductivity_normalized'], expected)

    def test_missing_temperature_handling(self):
        """Test handling of missing temperature values."""
        df = pd.DataFrame({
            'thermal_conductivity': [10.0, 15.0, 20.0],
            'temperature': [300.0, np.nan, 400.0]
        })

        result_df, warnings = normalize_dataframe(df)

        # Second row should have NaN for normalized value
        assert pd.isna(result_df.iloc[1]['thermal_conductivity_normalized'])
        assert len(warnings) == 1
        assert "Missing temperature" in warnings[0]

    def test_out_of_range_temperature_handling(self):
        """Test handling of out-of-range temperature values."""
        df = pd.DataFrame({
            'thermal_conductivity': [10.0, 15.0, 20.0],
            'temperature': [300.0, 40.0, 400.0]  # 40K is below MIN_VALID_TEMP_K
        })

        result_df, warnings = normalize_dataframe(df)

        # Second row should have NaN
        assert pd.isna(result_df.iloc[1]['thermal_conductivity_normalized'])
        assert any("outside valid range" in w for w in warnings)

    def test_missing_required_columns(self):
        """Test that missing required columns raise ValueError."""
        df = pd.DataFrame({
            'thermal_conductivity': [10.0, 15.0],
            'temp': [300.0, 400.0]  # Wrong column name
        })

        with pytest.raises(ValueError, match="not found"):
            normalize_dataframe(df, temp_col='temperature')

    def test_temperature_window_flag(self):
        """Test temperature_window_flag column."""
        df = pd.DataFrame({
            'thermal_conductivity': [10.0, 15.0, 20.0],
            'temperature': [300.0, 310.0, 350.0]  # 350 is outside window
        })

        result_df, warnings = normalize_dataframe(df)

        assert result_df.iloc[0]['temperature_window_flag'] is True
        assert result_df.iloc[1]['temperature_window_flag'] is True
        assert result_df.iloc[2]['temperature_window_flag'] is False

    def test_custom_column_names(self):
        """Test with custom column names."""
        df = pd.DataFrame({
            'kappa': [10.0, 15.0],
            'temp_k': [300.0, 400.0]
        })

        result_df, warnings = normalize_dataframe(
            df,
            kappa_col='kappa',
            temp_col='temp_k',
            output_col='kappa_norm'
        )

        assert 'kappa_norm' in result_df.columns
        assert result_df.iloc[1]['kappa_norm'] == 15.0 * (400.0 / 300.0)


class TestApplyTemperatureNormalization:
    """Tests for apply_temperature_normalization function."""

    def test_file_normalization(self):
        """Test normalization from file to file."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("thermal_conductivity,temperature\n")
            f.write("10.0,300.0\n")
            f.write("15.0,400.0\n")
            input_path = f.name

        # Output path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            result_path = apply_temperature_normalization(input_path, output_path)

            # Verify output file exists
            assert Path(result_path).exists()

            # Read and verify contents
            result_df = pd.read_csv(result_path)
            assert len(result_df) == 2
            assert 'thermal_conductivity_normalized' in result_df.columns

            # Verify normalization
            assert np.isclose(result_df.iloc[0]['thermal_conductivity_normalized'], 10.0)
            expected = 15.0 * (400.0 / 300.0)
            assert np.isclose(result_df.iloc[1]['thermal_conductivity_normalized'], expected)

        finally:
            # Cleanup
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_file_not_found(self):
        """Test that missing input file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            apply_temperature_normalization(
                "nonexistent_file.csv",
                "output.csv"
            )

    def test_missing_columns_in_file(self):
        """Test that missing columns in file raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("kappa,temperature\n")  # Wrong column name
            f.write("10.0,300.0\n")
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(ValueError, match="not found"):
                apply_temperature_normalization(input_path, output_path)
        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_creates_output_directory(self):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("thermal_conductivity,temperature\n")
            f.write("10.0,300.0\n")
            input_path = f.name

        output_dir = tempfile.mkdtemp()
        output_path = f"{output_dir}/subdir/output.csv"

        try:
            result_path = apply_temperature_normalization(input_path, output_path)
            assert Path(result_path).exists()
        finally:
            Path(input_path).unlink(missing_ok=True)
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)