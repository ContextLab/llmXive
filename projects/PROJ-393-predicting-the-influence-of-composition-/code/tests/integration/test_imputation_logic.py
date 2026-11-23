"""
Integration test for imputation logic (T015).

Tests the selection between Listwise Deletion (>15% missing) and Mean Imputation (<=15% missing)
as defined in Spec FR-002.

This test creates synthetic data scenarios to verify the orchestrator's decision logic
and the actual data transformation outcomes.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add src to path if not already present
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from preprocessing.imputation_orchestrator import ImputationOrchestrator


class TestImputationLogicIntegration:
    """Integration tests for the ImputationOrchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = ImputationOrchestrator()

    def test_mean_imputation_selected_low_missing_rate(self):
        """
        Test that Mean Imputation is selected when missing rate is <= 15%.
        Scenario: 10 rows, 1 column with 1 missing value (10% missing).
        """
        # Create data with 10% missing in 'coercivity'
        data = {
            'alloy_id': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10'],
            'coercivity': [100.0, 120.0, np.nan, 110.0, 105.0, 115.0, 108.0, 112.0, 109.0, 111.0],
            'saturation_mag': [50.0, 52.0, 51.0, 53.0, 50.5, 51.5, 50.8, 52.2, 50.9, 51.1]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_low_missing.csv"
            output_path = Path(tmpdir) / "output_low_missing.csv"
            df.to_csv(input_path, index=False)

            result_df, report = self.orchestrator.run(input_path, output_path)

            # Verify logic: 10% <= 15% -> Mean Imputation
            assert report['strategy'] == 'mean_imputation', f"Expected mean_imputation, got {report['strategy']}"
            assert report['missing_rate'] <= 0.15

            # Verify outcome: No NaNs in result, and the missing value is filled with mean
            assert not result_df['coercivity'].isna().any(), "Mean imputation should remove all NaNs"
            
            # Calculate expected mean of non-missing values
            expected_mean = df['coercivity'].mean()
            filled_value = result_df.loc[result_df['alloy_id'] == 'A3', 'coercivity'].values[0]
            
            # Allow small floating point tolerance
            assert np.isclose(filled_value, expected_mean, rtol=1e-5), \
                f"Filled value {filled_value} does not match expected mean {expected_mean}"

    def test_listwise_deletion_selected_high_missing_rate(self):
        """
        Test that Listwise Deletion is selected when missing rate is > 15%.
        Scenario: 10 rows, 1 column with 2 missing values (20% missing).
        """
        # Create data with 20% missing in 'coercivity'
        data = {
            'alloy_id': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10'],
            'coercivity': [100.0, np.nan, 120.0, 110.0, np.nan, 115.0, 108.0, 112.0, 109.0, 111.0],
            'saturation_mag': [50.0, 52.0, 51.0, 53.0, 50.5, 51.5, 50.8, 52.2, 50.9, 51.1]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_high_missing.csv"
            output_path = Path(tmpdir) / "output_high_missing.csv"
            df.to_csv(input_path, index=False)

            result_df, report = self.orchestrator.run(input_path, output_path)

            # Verify logic: 20% > 15% -> Listwise Deletion
            assert report['strategy'] == 'listwise_deletion', f"Expected listwise_deletion, got {report['strategy']}"
            assert report['missing_rate'] > 0.15

            # Verify outcome: Rows with NaNs are dropped
            # Original had 10 rows, 2 missing -> 8 rows expected
            assert len(result_df) == 8, f"Expected 8 rows after listwise deletion, got {len(result_df)}"
            
            # Verify the dropped IDs are correct (A2 and A5)
            assert 'A2' not in result_df['alloy_id'].values
            assert 'A5' not in result_df['alloy_id'].values
            assert not result_df['coercivity'].isna().any(), "Listwise deletion should remove all NaNs"

    def test_multiple_columns_mixed_missing_rates(self):
        """
        Test behavior when multiple columns have missing values.
        The orchestrator should apply the strategy based on the MAXIMUM missing rate across columns.
        """
        # Create data where 'coercivity' has 10% missing, but 'saturation_mag' has 30% missing
        data = {
            'alloy_id': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10'],
            'coercivity': [100.0, np.nan, 120.0, 110.0, 105.0, 115.0, 108.0, 112.0, 109.0, 111.0], # 10% missing
            'saturation_mag': [50.0, 52.0, 51.0, np.nan, np.nan, np.nan, 50.8, 52.2, 50.9, 51.1]  # 30% missing
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_mixed.csv"
            output_path = Path(tmpdir) / "output_mixed.csv"
            df.to_csv(input_path, index=False)

            result_df, report = self.orchestrator.run(input_path, output_path)

            # Since max missing rate is 30% (>15%), Listwise Deletion must be used
            assert report['strategy'] == 'listwise_deletion', \
                f"Expected listwise_deletion due to max missing rate > 15%, got {report['strategy']}"

            # All rows with ANY missing value should be dropped
            # A2 (missing coercivity), A4, A5, A6 (missing saturation_mag) -> 6 rows dropped, 4 left
            assert len(result_df) == 4, f"Expected 4 rows, got {len(result_df)}"

    def test_zero_missing_rate(self):
        """Test that no imputation is needed when there are no missing values."""
        data = {
            'alloy_id': ['A1', 'A2', 'A3'],
            'coercivity': [100.0, 120.0, 110.0],
            'saturation_mag': [50.0, 52.0, 51.0]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_clean.csv"
            output_path = Path(tmpdir) / "output_clean.csv"
            df.to_csv(input_path, index=False)

            result_df, report = self.orchestrator.run(input_path, output_path)

            assert report['strategy'] == 'none', f"Expected 'none', got {report['strategy']}"
            assert report['missing_rate'] == 0.0
            pd.testing.assert_frame_equal(result_df, df)

    def test_report_structure(self):
        """Verify the structure of the returned report dictionary."""
        data = {
            'alloy_id': ['A1', 'A2', 'A3'],
            'coercivity': [100.0, np.nan, 110.0],
            'saturation_mag': [50.0, 52.0, 51.0]
        }
        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input_report_test.csv"
            output_path = Path(tmpdir) / "output_report_test.csv"
            df.to_csv(input_path, index=False)

            _, report = self.orchestrator.run(input_path, output_path)

            required_keys = ['strategy', 'missing_rate', 'rows_before', 'rows_after', 'columns_affected']
            for key in required_keys:
                assert key in report, f"Report missing required key: {key}"

            assert isinstance(report['rows_before'], int)
            assert isinstance(report['rows_after'], int)
            assert isinstance(report['missing_rate'], float)
            assert isinstance(report['columns_affected'], list)
            assert report['rows_after'] <= report['rows_before']