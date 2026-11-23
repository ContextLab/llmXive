import pytest
import numpy as np
import pandas as pd
from data.process import filter_trials

class TestTrialFilteringLatencyBounds:
    """
    Unit test for trial filtering: test_trial_filtering_latency_bounds.
    Assertion: Trials <300ms or >10000ms are excluded.
    """

    def test_trial_filtering_latency_bounds(self):
        """
        Verify that trials with latency < 300ms or > 10000ms are excluded.
        """
        # Create a synthetic DataFrame with various latency values
        data = {
            'participant_id': ['P1'] * 6,
            'session_id': ['S1'] * 6,
            'trial_id': [1, 2, 3, 4, 5, 6],
            'latency': [200, 299, 300, 5000, 10000, 10001],  # ms
            'correct': [1, 1, 1, 1, 1, 1],
            'block': ['A'] * 6,
            'stimulus': ['S'] * 6,
            'response': ['R'] * 6,
            'timestamp': pd.to_datetime(['2023-01-01'] * 6)
        }
        df = pd.DataFrame(data)

        # Apply the filter
        filtered_df = filter_trials(df)

        # Expected: Only trials with 300 <= latency <= 10000 should remain
        # Indices 2, 3, 4 correspond to latencies 300, 5000, 10000
        expected_indices = [2, 3, 4]
        expected_len = 3

        # Assert the length of the filtered dataframe
        assert len(filtered_df) == expected_len, (
            f"Expected {expected_len} trials, got {len(filtered_df)}. "
            f"Trials <300ms or >10000ms were not correctly excluded."
        )

        # Assert the specific indices/latencies remain
        assert list(filtered_df.index) == expected_indices, (
            f"Expected indices {expected_indices}, got {list(filtered_df.index)}."
        )

        # Assert the latencies in the result are within bounds
        assert all((filtered_df['latency'] >= 300) & (filtered_df['latency'] <= 10000)), (
            "Filtered dataframe contains trials outside the valid latency bounds [300, 10000]."
        )

        # Assert that the excluded trials are indeed the ones outside bounds
        excluded_latencies = df.loc[[0, 1, 5], 'latency'].tolist()
        assert 200 in excluded_latencies
        assert 299 in excluded_latencies
        assert 10001 in excluded_latencies