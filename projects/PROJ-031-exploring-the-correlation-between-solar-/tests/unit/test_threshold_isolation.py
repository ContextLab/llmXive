import pytest
import pandas as pd
import os
import sys
from datetime import datetime

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis import validate_timeseries_split, run_correlation_analysis

class TestThresholdValidationIsolation:
    """
    Tests to ensure threshold sensitivity analysis (T034b) strictly uses
    only the hold-out set (2021-2023) and does not leak training data.
    """

    def test_timeseries_split_enforcement(self):
        """
        Verify that validate_timeseries_split correctly separates data
        into train (<=2020) and test (>2020) sets.
        """
        # Create synthetic test data spanning 2019-2022
        data = {
            'date': pd.to_datetime([
                '2019-06-01', '2020-12-31', '2021-01-01', '2021-06-15',
                '2022-01-01', '2023-06-01'
            ]),
            'value': [1, 2, 3, 4, 5, 6],
            'dst': [-10, -20, -30, -40, -50, -60],
            'cme_speed': [500, 600, 700, 800, 900, 1000]
        }
        df = pd.DataFrame(data)

        train_df, test_df = validate_timeseries_split(df, train_end="2020-12-31")

        # Assertions
        assert len(train_df) == 2, f"Expected 2 train rows, got {len(train_df)}"
        assert len(test_df) == 4, f"Expected 4 test rows, got {len(test_df)}"

        # Verify dates
        assert train_df['date'].max() <= pd.Timestamp("2020-12-31")
        assert test_df['date'].min() > pd.Timestamp("2020-12-31")

        # Ensure no overlap
        train_dates = set(train_df['date'].dt.date)
        test_dates = set(test_df['date'].dt.date)
        assert len(train_dates.intersection(test_dates)) == 0, "Date overlap detected between train and test sets."

    def test_analysis_function_uses_holdout_only(self):
        """
        Verify that the analysis logic (specifically for threshold sensitivity)
        would only receive the hold-out set when called with the correct split.
        This test simulates the isolation requirement.
        """
        # Create full dataset
        full_data = {
            'date': pd.to_datetime([
                '2010-01-01', '2015-06-01', '2020-12-31', # Train
                '2021-01-01', '2022-06-01', '2023-12-31'  # Test
            ]),
            'cme_speed': [300, 400, 500, 800, 900, 1000],
            'dst': [-10, -20, -30, -50, -60, -70],
            'log_flare_flux': [1, 2, 3, 4, 5, 6]
        }
        df_full = pd.DataFrame(full_data)

        # Split
        train_df, test_df = validate_timeseries_split(df_full, train_end="2020-12-31")

        # Verify test_df contains ONLY 2021-2023 data
        assert test_df['date'].min() >= pd.Timestamp("2021-01-01")
        assert test_df['date'].max() <= pd.Timestamp("2023-12-31")

        # Verify train_df contains ONLY <=2020 data
        assert train_df['date'].max() <= pd.Timestamp("2020-12-31")

        # Simulate that the threshold analysis (T034b) runs ONLY on test_df
        # We check that the function run_correlation_analysis can run on test_df
        # without accessing train_df (by design, it only takes one df)
        # The isolation is enforced by the caller passing only test_df.
        # This test verifies the split is correct so the caller CAN enforce isolation.
        assert len(test_df) > 0, "Test set is empty, cannot validate isolation."

    def test_no_leakage_in_sensitivity_sweep(self):
        """
        Explicit test to ensure that if we were to run a sensitivity sweep
        on the test set, no data from the train set is accessible.
        """
        # Create data
        train_data = pd.DataFrame({
            'date': pd.to_datetime(['2010-01-01', '2020-12-31']),
            'cme_speed': [100, 200],
            'dst': [-5, -10]
        })
        test_data = pd.DataFrame({
            'date': pd.to_datetime(['2021-01-01', '2023-12-31']),
            'cme_speed': [800, 900],
            'dst': [-50, -60]
        })

        # The sensitivity sweep logic (T034b) would operate on `test_data`
        # We verify that `train_data` is not mixed in.
        combined = pd.concat([train_data, test_data], ignore_index=True)
        split_train, split_test = validate_timeseries_split(combined, train_end="2020-12-31")

        # Ensure split_test matches test_data content (approx)
        assert set(split_test['date']) == set(test_data['date'])
        assert set(split_train['date']) == set(train_data['date'])

        # Verify that if we run analysis on split_test, it doesn't see train_data
        # (This is implicit in the function signature, but we assert the data integrity)
        assert '2010-01-01' not in split_test['date'].astype(str).values
        assert '2020-12-31' not in split_test['date'].astype(str).values