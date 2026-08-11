"""
Unit tests for temperature normalization module.

Tests for Slack (1979) formula implementation and edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from cleaning.temperature_normalize import (
    slack_normalization_factor,
    normalize_thermal_conductivity,
    is_within_reference_window,
    normalize_dataframe,
    apply_temperature_normalization,
    REFERENCE_TEMPERATURE_K,
    TEMP_WINDOW_TOLERANCE_K
)
from utils.validation import setup_logger


class TestSlackNormalizationFactor:
    """Tests for the Slack normalization factor calculation."""

    def test_factor_at_reference_temperature(self):
        """Factor should be 1.0 when measured temp equals reference temp."""
        factor = slack_normalization_factor(300.0, 300.0)
        assert factor == pytest.approx(1.0, rel=1e-6)

    def test_factor_higher_temperature(self):
        """Factor should be < 1.0 when T_meas > T_ref (conductivity decreases with T)."""
        # κ ∝ T^-1, so κ(400) = κ(300) * (300/400)^1 = 0.75 * κ(300)
        # Factor to get back to 300K: (400/300)^1 = 1.333...
        # Wait, our formula: factor = (T_meas / T_ref)^exponent
        # If T_meas = 400, T_ref = 300, factor = (400/300)^1 = 1.333
        # Then κ_norm = κ_meas * 1.333
        # This assumes κ_meas is lower at higher T, so we multiply to get back up.
        factor = slack_normalization_factor(400.0, 300.0)
        assert factor == pytest.approx(4.0/3.0, rel=1e-6)

    def test_factor_lower_temperature(self):
        """Factor should be > 1.0 when T_meas < T_ref."""
        # T_meas = 200, T_ref = 300 -> factor = (200/300)^1 = 0.666
        # κ_norm = κ_meas * 0.666
        # If κ is higher at lower T, we multiply by < 1 to normalize down.
        factor = slack_normalization_factor(200.0, 300.0)
        assert factor == pytest.approx(2.0/3.0, rel=1e-6)

    def test_invalid_negative_temperature(self):
        """Should raise ValueError for negative temperature."""
        with pytest.raises(ValueError, match="positive"):
            slack_normalization_factor(-10.0, 300.0)

    def test_invalid_zero_temperature(self):
        """Should raise ValueError for zero temperature."""
        with pytest.raises(ValueError, match="positive"):
            slack_normalization_factor(0.0, 300.0)


class TestNormalizeThermalConductivity:
    """Tests for the full normalization calculation."""

    def test_normalize_at_reference(self):
        """Value at reference temp should remain unchanged."""
        k_measured = 5.0
        k_normalized = normalize_thermal_conductivity(k_measured, 300.0, 300.0)
        assert k_normalized == pytest.approx(5.0, rel=1e-6)

    def test_normalize_high_temperature(self):
        """Normalize a value measured at higher temperature."""
        # If κ ∝ T^-1, and we measure 2.0 W/mK at 400K:
        # κ(300) = 2.0 * (400/300)^1 = 2.0 * 1.333 = 2.666
        k_measured = 2.0
        temp_measured = 400.0
        k_normalized = normalize_thermal_conductivity(k_measured, temp_measured, 300.0)
        expected = 2.0 * (400.0 / 300.0)
        assert k_normalized == pytest.approx(expected, rel=1e-6)

    def test_normalize_low_temperature(self):
        """Normalize a value measured at lower temperature."""
        # If we measure 8.0 W/mK at 200K:
        # κ(300) = 8.0 * (200/300)^1 = 8.0 * 0.666 = 5.333
        k_measured = 8.0
        temp_measured = 200.0
        k_normalized = normalize_thermal_conductivity(k_measured, temp_measured, 300.0)
        expected = 8.0 * (200.0 / 300.0)
        assert k_normalized == pytest.approx(expected, rel=1e-6)


class TestIsWithinReferenceWindow:
    """Tests for temperature window checking."""

    def test_within_window_upper_bound(self):
        """310K should be within 300K ± 10K."""
        assert is_within_reference_window(310.0, 300.0, 10.0)

    def test_within_window_lower_bound(self):
        """290K should be within 300K ± 10K."""
        assert is_within_reference_window(290.0, 300.0, 10.0)

    def test_outside_window_high(self):
        """311K should be outside 300K ± 10K."""
        assert not is_within_reference_window(311.0, 300.0, 10.0)

    def test_outside_window_low(self):
        """289K should be outside 300K ± 10K."""
        assert not is_within_reference_window(289.0, 300.0, 10.0)

    def test_exact_center(self):
        """300K should be within window."""
        assert is_within_reference_window(300.0, 300.0, 10.0)


class TestNormalizeDataFrame:
    """Tests for DataFrame normalization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.df = pd.DataFrame({
            'thermal_conductivity': [5.0, 2.0, 8.0, 4.0, np.nan],
            'measurement_temperature': [300.0, 400.0, 200.0, np.nan, 305.0],
            'material_id': ['MP-1', 'MP-2', 'MP-3', 'MP-4', 'MP-5']
        })

    def test_normalization_creates_column(self):
        """Should create a new normalized column."""
        df_norm, normalized_idx, unknown_idx = normalize_dataframe(
            self.df.copy(), 'thermal_conductivity', 'measurement_temperature'
        )
        assert 'thermal_conductivity_normalized_300K' in df_norm.columns

    def test_within_window_keeps_value(self):
        """Rows within window should keep original value."""
        df_norm, _, _ = normalize_dataframe(
            self.df.copy(), 'thermal_conductivity', 'measurement_temperature'
        )
        # MP-1 at 300K and MP-5 at 305K are within window
        assert df_norm.loc[0, 'thermal_conductivity_normalized_300K'] == pytest.approx(5.0)
        assert df_norm.loc[4, 'thermal_conductivity_normalized_300K'] == pytest.approx(4.0)

    def test_outside_window_normalizes(self):
        """Rows outside window should be normalized."""
        df_norm, normalized_idx, _ = normalize_dataframe(
            self.df.copy(), 'thermal_conductivity', 'measurement_temperature'
        )
        # MP-2 at 400K: 2.0 * (400/300) = 2.666
        assert df_norm.loc[1, 'thermal_conductivity_normalized_300K'] == pytest.approx(2.666, rel=1e-3)
        # MP-3 at 200K: 8.0 * (200/300) = 5.333
        assert df_norm.loc[2, 'thermal_conductivity_normalized_300K'] == pytest.approx(5.333, rel=1e-3)

    def test_unknown_temperature_flagged(self):
        """Rows with NaN temperature should be flagged."""
        df_norm, _, unknown_idx = normalize_dataframe(
            self.df.copy(), 'thermal_conductivity', 'measurement_temperature'
        )
        assert 3 in unknown_idx
        assert pd.isna(df_norm.loc[3, 'thermal_conductivity_normalized_300K'])

    def test_missing_k_value_handled(self):
        """Rows with NaN conductivity should be skipped."""
        df_norm, _, _ = normalize_dataframe(
            self.df.copy(), 'thermal_conductivity', 'measurement_temperature'
        )
        assert pd.isna(df_norm.loc[4, 'thermal_conductivity_normalized_300K'])

    def test_missing_columns_raises(self):
        """Should raise ValueError if columns are missing."""
        with pytest.raises(ValueError, match="not found"):
            normalize_dataframe(
                self.df.copy(), 'wrong_col', 'measurement_temperature'
            )
        with pytest.raises(ValueError, match="not found"):
            normalize_dataframe(
                self.df.copy(), 'thermal_conductivity', 'wrong_col'
            )


class TestApplyTemperatureNormalization:
    """Tests for the file-based normalization entry point."""

    def test_full_file_normalization(self):
        """Test end-to-end file normalization."""
        input_df = pd.DataFrame({
            'thermal_conductivity': [5.0, 2.0, 8.0],
            'measurement_temperature': [300.0, 400.0, 200.0],
            'material_id': ['A', 'B', 'C']
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            input_df.to_csv(input_path, index=False)

            apply_temperature_normalization(
                str(input_path), str(output_path),
                k_col='thermal_conductivity',
                temp_col='measurement_temperature'
            )

            assert output_path.exists()
            result_df = pd.read_csv(output_path)
            assert 'thermal_conductivity_normalized_300K' in result_df.columns
            assert len(result_df) == 3

    def test_missing_input_file_raises(self):
        """Should raise FileNotFoundError for missing input."""
        with pytest.raises(FileNotFoundError):
            apply_temperature_normalization(
                "nonexistent.csv", "output.csv"
            )

    def test_strict_mode_no_data_raises(self):
        """Should raise ValueError in strict mode if no data can be normalized."""
        input_df = pd.DataFrame({
            'thermal_conductivity': [5.0, 2.0],
            'measurement_temperature': [np.nan, np.nan],
            'material_id': ['A', 'B']
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            input_df.to_csv(input_path, index=False)

            with pytest.raises(ValueError, match="No valid data"):
                apply_temperature_normalization(
                    str(input_path), str(output_path),
                    strict_mode=True
                )

    def test_non_strict_mode_no_data(self):
        """Should not raise in non-strict mode if no data can be normalized."""
        input_df = pd.DataFrame({
            'thermal_conductivity': [5.0, 2.0],
            'measurement_temperature': [np.nan, np.nan],
            'material_id': ['A', 'B']
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"

            input_df.to_csv(input_path, index=False)

            # Should not raise
            apply_temperature_normalization(
                str(input_path), str(output_path),
                strict_mode=False
            )
            assert output_path.exists()