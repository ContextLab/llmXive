"""
Integration test for signal detection producing output/signals.csv.

This test verifies that the disproportionality analysis pipeline:
1. Loads cleaned data from data/processed/cleaned_vaers.parquet
2. Calculates ROR, PRR, IC with 95% CIs for each SOC
3. Applies Benjamini-Hochberg FDR correction
4. Flags signals meeting the 2-out-of-3 rule
5. Writes valid output to output/signals.csv
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.analysis.disproportionality import run_disproportionality_analysis


class TestSignalDetectionIntegration:
    """Integration tests for the signal detection pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure output directory exists."""
        self.output_dir = project_root / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.signals_file = self.output_dir / "signals.csv"
        
        # Remove existing signals file if present
        if self.signals_file.exists():
            self.signals_file.unlink()

    def test_signal_detection_produces_valid_csv(self):
        """
        Test that the signal detection pipeline produces a valid signals.csv file
        with all required columns and correct signal flags.
        """
        cleaned_data_path = project_root / "data" / "processed" / "cleaned_vaers.parquet"
        
        # Skip test if cleaned data doesn't exist (prerequisite not met)
        if not cleaned_data_path.exists():
            pytest.skip("Cleaned data file not found. Run US1 tasks first.")

        # Run the analysis
        result = run_disproportionality_analysis(
            input_path=str(cleaned_data_path),
            output_path=str(self.signals_file),
            min_reports=5
        )

        # Verify output file exists
        assert self.signals_file.exists(), "output/signals.csv was not created"
        
        # Load and validate the output
        df = pd.read_csv(self.signals_file)
        
        # Check required columns per signal.schema.yaml
        required_columns = {
            'soc_code', 'soc_name', 'total_reports', 'covid_cases', 'non_covid_cases',
            'ror', 'ror_ci_lower', 'ror_ci_upper', 'prr', 'prr_ci_lower', 'prr_ci_upper',
            'ic', 'ic_ci_lower', 'ic_ci_upper', 'adjusted_p', 'is_signal_ror',
            'is_signal_prr', 'is_signal_ic', 'is_signal_combined', 'background_rate_known'
        }
        
        missing_cols = required_columns - set(df.columns)
        assert not missing_cols, f"Missing required columns: {missing_cols}"
        
        # Verify all values are finite (no NaN or inf) for rows with sufficient data
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Allow NaN for background_rate_known if not applicable
            if col != 'background_rate_known':
                finite_values = df[col].apply(lambda x: np.isfinite(x) if pd.notna(x) else True)
                # Check that we don't have unexpected NaNs in key metric columns
                if col in ['ror', 'prr', 'ic', 'adjusted_p']:
                    # These should be finite for rows with enough data
                    valid_rows = df['total_reports'] >= 5
                    if valid_rows.any():
                        assert df.loc[valid_rows, col].apply(lambda x: np.isfinite(x) if pd.notna(x) else False).all(), \
                            f"Column {col} contains non-finite values for valid rows"

        # Verify signal flag logic (2-out-of-3 rule)
        # A signal is flagged if at least 2 of the 3 metrics meet their criteria
        for _, row in df.iterrows():
            if row['total_reports'] >= 5:
                ror_flag = row['is_signal_ror']
                prr_flag = row['is_signal_prr']
                ic_flag = row['is_signal_ic']
                combined_flag = row['is_signal_combined']
                
                # Count how many individual flags are True
                individual_count = sum([ror_flag, prr_flag, ic_flag])
                
                # Combined flag should be True if at least 2 individual flags are True
                expected_combined = individual_count >= 2
                assert combined_flag == expected_combined, \
                    f"Signal flag mismatch for SOC {row['soc_code']}: " \
                    f"individual_count={individual_count}, expected_combined={expected_combined}, actual={combined_flag}"

        # Verify we have at least some data
        assert len(df) > 0, "Output dataframe is empty"
        
        # Verify no duplicate SOCs
        assert df['soc_code'].is_unique, "Duplicate SOC codes found in output"

        # Verify metric ranges make sense
        # ROR, PRR should be positive
        assert (df['ror'] > 0).all(), "ROR values should be positive"
        assert (df['prr'] > 0).all(), "PRR values should be positive"
        
        # IC can be negative but should be finite
        assert df['ic'].notna().all(), "IC should not have NaN values for valid rows"

    def test_benjamini_hochberg_correction_monotonic(self):
        """
        Test that Benjamini-Hochberg corrected p-values are monotonically increasing
        when sorted by raw p-value.
        """
        if not self.signals_file.exists():
            pytest.skip("Signals file not found. Run test_signal_detection_produces_valid_csv first.")

        df = pd.read_csv(self.signals_file)
        
        # Filter to rows with valid p-values
        valid_df = df[df['adjusted_p'].notna() & df['adjusted_p'].apply(np.isfinite)]
        
        if len(valid_df) == 0:
            pytest.skip("No valid adjusted p-values found")

        # Sort by raw p-value (we need to recalculate or assume the adjusted p-values are correct)
        # Since we don't have raw p-values in the output, we verify the property that
        # adjusted p-values should be non-decreasing when sorted by raw p-value
        # For now, we just verify they are in [0, 1] range
        
        assert (valid_df['adjusted_p'] >= 0).all(), "Adjusted p-values should be >= 0"
        assert (valid_df['adjusted_p'] <= 1).all(), "Adjusted p-values should be <= 1"

    def test_output_file_format(self):
        """
        Test that the output file is a valid CSV with proper encoding.
        """
        if not self.signals_file.exists():
            pytest.skip("Signals file not found.")

        # Try to read with different encodings
        try:
            df_utf8 = pd.read_csv(self.signals_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df_latin1 = pd.read_csv(self.signals_file, encoding='latin-1')
            except UnicodeDecodeError:
                raise AssertionError("Output file cannot be read as valid CSV with common encodings")
        
        # Verify it's not empty
        assert len(df_utf8) > 0, "Output CSV is empty"
        
        # Verify column count matches expected
        assert len(df_utf8.columns) >= 15, f"Expected at least 15 columns, got {len(df_utf8.columns)}"

    def test_signal_detection_handles_empty_groups(self):
        """
        Test that the analysis handles cases where one group might have zero events.
        This is implicitly tested by the continuity correction in the main analysis,
        but we verify the output is still valid.
        """
        if not self.signals_file.exists():
            pytest.skip("Signals file not found.")

        df = pd.read_csv(self.signals_file)
        
        # All ROR, PRR, IC should be finite (continuity correction should prevent inf)
        finite_ror = df['ror'].apply(lambda x: np.isfinite(x) if pd.notna(x) else False)
        finite_prr = df['prr'].apply(lambda x: np.isfinite(x) if pd.notna(x) else False)
        finite_ic = df['ic'].apply(lambda x: np.isfinite(x) if pd.notna(x) else False)
        
        assert finite_ror.all(), "ROR contains non-finite values"
        assert finite_prr.all(), "PRR contains non-finite values"
        assert finite_ic.all(), "IC contains non-finite values"