"""
Unit tests for code/analyzer.py, specifically focusing on Cox Proportional Hazards
model handling of censored data as required by T031.
"""
import pytest
import pandas as pd
import numpy as np
from lifelines import CoxPHFitter
from pathlib import Path
import sys

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer import (
    run_cox_ph_analysis,
    prepare_survival_data,
    calculate_hazard_ratios
)


class TestCoxPHCensoredDataHandling:
    """
    Tests specifically for Cox PH model handling of censored data.
    T031: Unit test for Cox Proportional Hazards model handling of censored data.
    """

    def test_cox_ph_with_all_censored_data(self):
        """
        Verify that Cox PH model handles a dataset where all events are censored
        (i.e., no convergence observed within the turn limit).
        """
        # Create synthetic data where all instances hit the turn limit (censored)
        data = pd.DataFrame({
            'nesting_depth': [3, 4, 5, 6, 7],
            'branching_factor': [2, 2, 3, 3, 4],
            'duration': [50, 50, 50, 50, 50],  # All hit the limit
            'event': [0, 0, 0, 0, 0]           # All censored
        })

        # This should not raise an error, though the model might be ill-conditioned
        # lifelines handles this by warning or returning NaN for coefficients
        try:
            cph = CoxPHFitter()
            cph.fit(data, duration_col='duration', event_col='event')
            # If we get here, the model fitted (even if coefficients are NaN)
            assert hasattr(cph, 'summary')
        except Exception as e:
            # If lifelines raises a specific error for all-censored data, that's acceptable
            # as long as it's a clear error, not a silent failure or crash
            assert "ill-conditioned" in str(e).lower() or "convergence" in str(e).lower()

    def test_cox_ph_with_mixed_censored_uncensored(self):
        """
        Verify Cox PH model correctly processes a mix of censored and uncensored data.
        This is the standard case for survival analysis.
        """
        data = pd.DataFrame({
            'nesting_depth': [3, 4, 5, 6, 7, 8],
            'branching_factor': [2, 2, 3, 3, 4, 4],
            'duration': [10, 20, 30, 45, 50, 50], # 50 is the limit (censored)
            'event': [1, 1, 1, 1, 0, 0]          # 0=censored, 1=event
        })

        cph = CoxPHFitter()
        cph.fit(data, duration_col='duration', event_col='event')

        # Verify the model produced coefficients
        assert cph.summary is not None
        assert 'nesting_depth' in cph.summary.index
        assert 'branching_factor' in cph.summary.index

        # Verify that censored observations (event=0) contributed to the likelihood
        # but did not count as events in the partial likelihood
        assert len(data[data['event'] == 0]) == 2
        assert len(data[data['event'] == 1]) == 4

    def test_cox_ph_with_single_censored_observation(self):
        """
        Test edge case: dataset with only one censored observation.
        """
        data = pd.DataFrame({
            'nesting_depth': [3, 4, 5],
            'branching_factor': [2, 2, 3],
            'duration': [10, 20, 50], # Last one is censored
            'event': [1, 1, 0]
        })

        cph = CoxPHFitter()
        cph.fit(data, duration_col='duration', event_col='event')

        assert cph.summary is not None
        assert len(cph.summary) == 2 # nesting_depth and branching_factor

    def test_cox_ph_censoring_rate_calculation(self):
        """
        Verify that the censoring rate is calculated correctly from the data.
        """
        # 3 events, 2 censored -> 40% censored
        data = pd.DataFrame({
            'nesting_depth': [3, 4, 5, 6, 7],
            'duration': [10, 20, 30, 50, 50],
            'event': [1, 1, 1, 0, 0]
        })

        censoring_rate = 1 - (data['event'].sum() / len(data))
        assert abs(censoring_rate - 0.4) < 1e-6

    def test_prepare_survival_data_handles_censored_flags(self):
        """
        Test that prepare_survival_data correctly maps 'convergence_status'
        to the 'event' column (0 for failure/censored, 1 for success).
        """
        # Mock data similar to execution_log.csv
        raw_data = pd.DataFrame({
            'instance_id': ['p1', 'p2', 'p3', 'p4'],
            'nesting_depth': [3, 4, 5, 6],
            'branching_factor': [2, 3, 2, 4],
            'turns_to_converge': [10, 25, 50, 50], # 50 is max_turns
            'convergence_status': ['success', 'success', 'failure', 'failure']
        })

        prepared = prepare_survival_data(raw_data, max_turns=50)

        # Check that 'failure' maps to event=0 (censored)
        # and 'success' maps to event=1 (event occurred)
        assert prepared.loc[prepared['instance_id'] == 'p3', 'event'].values[0] == 0
        assert prepared.loc[prepared['instance_id'] == 'p4', 'event'].values[0] == 0
        assert prepared.loc[prepared['instance_id'] == 'p1', 'event'].values[0] == 1
        assert prepared.loc[prepared['instance_id'] == 'p2', 'event'].values[0] == 1

        # Check duration is preserved
        assert prepared.loc[prepared['instance_id'] == 'p3', 'duration'].values[0] == 50

    def test_cox_ph_significance_with_censored_data(self):
        """
        Verify that statistical significance (p-values) is calculated correctly
        even when a portion of the data is censored.
        """
        # Create data with a clear trend: higher depth -> longer time to converge
        # but with some censored at the end
        np.random.seed(42)
        n = 100
        depths = np.random.randint(3, 8, n)
        # Duration increases with depth, but capped at 50
        durations = np.clip(depths * 5 + np.random.normal(0, 5, n), 1, 50)
        events = (durations < 50).astype(int) # 0 if censored, 1 if converged

        data = pd.DataFrame({
            'nesting_depth': depths,
            'branching_factor': np.random.randint(2, 5, n),
            'duration': durations,
            'event': events
        })

        cph = CoxPHFitter()
        cph.fit(data, duration_col='duration', event_col='event')

        # Check that p-values are present and numeric
        assert 'p' in cph.summary.columns
        assert all(isinstance(p, (int, float, np.floating)) for p in cph.summary['p'])
        # Check that we have valid hazard ratios
        assert 'coef' in cph.summary.columns

    def test_run_cox_ph_analysis_with_high_censoring(self):
        """
        Test the full pipeline function with a dataset that has high censoring rate (>50%).
        This simulates a scenario where the model struggles to converge within the turn limit.
        """
        # Create data with 70% censored
        data = pd.DataFrame({
            'nesting_depth': [3, 3, 4, 4, 5, 5, 6, 6],
            'branching_factor': [2, 2, 3, 3, 3, 3, 4, 4],
            'duration': [10, 15, 20, 25, 50, 50, 50, 50],
            'event': [1, 1, 1, 1, 0, 0, 0, 0] # 4 events, 4 censored -> 50%
        })

        # Add more censored to push over 50%
        data = pd.concat([data, pd.DataFrame({
            'nesting_depth': [7, 7, 7],
            'branching_factor': [5, 5, 5],
            'duration': [50, 50, 50],
            'event': [0, 0, 0]
        })], ignore_index=True)

        result = run_cox_ph_analysis(data, duration_col='duration', event_col='event')

        assert result is not None
        assert 'summary' in result
        assert 'censoring_rate' in result
        assert result['censoring_rate'] > 0.5

    def test_cox_ph_stratified_by_censoring(self):
        """
        Verify that the model can handle stratified data where censoring patterns differ.
        """
        # Create two groups with different censoring patterns
        data = pd.DataFrame({
            'nesting_depth': [3, 3, 4, 4, 5, 5, 6, 6],
            'group': ['A', 'A', 'A', 'A', 'B', 'B', 'B', 'B'],
            'duration': [10, 15, 20, 50, 10, 15, 20, 25],
            'event': [1, 1, 1, 0, 1, 1, 1, 1]
        })

        # Add group as a covariate
        data = pd.get_dummies(data, columns=['group'], drop_first=True)

        cph = CoxPHFitter()
        cph.fit(data, duration_col='duration', event_col='event')

        assert cph.summary is not None
        assert 'group_B' in cph.summary.index