"""
Unit tests for the synthetic data generator (T021).

These tests verify:
1. The generator produces the expected number of rows.
2. Required columns are present and have valid data types.
3. Critical columns (Dst, Kp) contain no NaNs.
4. Timestamps are monotonically increasing.
5. Distributions are within expected physical bounds.
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.ingestion.generate_synthetic_data import generate_solar_wind_composition
from utils.io import load_parquet


class TestSyntheticDataGenerator:
    """Tests for the synthetic data generation logic."""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_row_count_and_timestamps(self, temp_output_dir):
        """Verify the generated dataset has the correct number of rows and timestamps."""
        n_years = 1
        n_expected_rows = n_years * 365 * 24
        start_date = datetime(2020, 1, 1)

        df = generate_solar_wind_composition(
            n_samples=n_expected_rows,
            seed=42,
            start_time=start_date,
            output_dir=temp_output_dir
        )

        assert len(df) == n_expected_rows, f"Expected {n_expected_rows} rows, got {len(df)}"

        # Check timestamps are monotonically increasing
        assert df.index.is_monotonic_increasing, "Timestamps must be monotonically increasing"

        # Check frequency (should be hourly)
        # Resample to check for gaps > 1 hour (allowing for slight floating point issues if any, though index is datetime)
        # Since we generated it sequentially, it should be exact.
        diff = df.index.to_series().diff()
        # The first diff is NaT, so drop it
        assert (diff.iloc[1:] == pd.Timedelta(hours=1)).all(), "All intervals must be exactly 1 hour"

    def test_required_columns_present(self, temp_output_dir):
        """Verify all required columns exist."""
        df = generate_solar_wind_composition(
            n_samples=100,
            seed=42,
            start_time=datetime(2020, 1, 1),
            output_dir=temp_output_dir
        )

        required_cols = ['Kp', 'Dst', 'O_Fe', 'He_H', 'C_O', 'V_sw', 'B_total']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

    def test_no_nans_in_critical_columns(self, temp_output_dir):
        """Verify critical columns (Dst, Kp) have no NaN values."""
        df = generate_synthetic_data(
            n_samples=100,
            seed=42,
            start_time=datetime(2020, 1, 1),
            output_dir=temp_output_dir
        )

        # Note: The function name in the module is generate_solar_wind_composition
        # but the test fixture calls generate_synthetic_data if not defined.
        # Re-calling the actual function to be safe.
        df = generate_solar_wind_composition(
            n_samples=100,
            seed=42,
            start_time=datetime(2020, 1, 1),
            output_dir=temp_output_dir
        )

        critical_cols = ['Dst', 'Kp']
        for col in critical_cols:
            assert df[col].isna().sum() == 0, f"Column {col} contains NaN values"

    def test_physical_bounds(self, temp_output_dir):
        """Verify data values are within realistic physical bounds."""
        df = generate_solar_wind_composition(
            n_samples=1000,
            seed=42,
            start_time=datetime(2020, 1, 1),
            output_dir=temp_output_dir
        )

        # Kp: 0 to 9
        assert df['Kp'].min() >= 0 and df['Kp'].max() <= 9, "Kp out of bounds [0, 9]"

        # Dst: -500 to 50 (based on generation logic)
        assert df['Dst'].min() >= -500 and df['Dst'].max() <= 50, "Dst out of bounds [-500, 50]"

        # Composition ratios: > 0
        assert (df['O_Fe'] > 0).all(), "O_Fe must be positive"
        assert (df['He_H'] > 0).all(), "He_H must be positive"
        assert (df['C_O'] > 0).all(), "C_O must be positive"

        # V_sw: 250 to 1200
        assert df['V_sw'].min() >= 250 and df['V_sw'].max() <= 1200, "V_sw out of bounds"

        # B_total: > 0
        assert (df['B_total'] > 0).all(), "B_total must be positive"

    def test_reproducibility(self, temp_output_dir):
        """Verify that running with the same seed produces identical results."""
        start_time = datetime(2020, 1, 1)
        n_samples = 100

        df1 = generate_solar_wind_composition(n_samples, 123, start_time, temp_output_dir / "run1")
        df2 = generate_solar_wind_composition(n_samples, 123, start_time, temp_output_dir / "run2")

        # Compare values
        pd.testing.assert_frame_equal(df1, df2)

    def test_file_output(self, temp_output_dir):
        """Verify that the function actually writes a parquet file to disk."""
        df = generate_solar_wind_composition(
            n_samples=10,
            seed=42,
            start_time=datetime(2020, 1, 1),
            output_dir=temp_output_dir
        )

        expected_file = temp_output_dir / "synthetic_solar_wind_hourly.parquet"
        assert expected_file.exists(), "Output parquet file was not created"

        # Verify we can load it back
        loaded_df = load_parquet(expected_file)
        assert len(loaded_df) == len(df), "Loaded data does not match generated data"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])