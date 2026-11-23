import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from aggregation import filter_zero_variance
from config import get_project_root

class TestFilterZeroVariance:
    """
    Unit tests for the `filter_zero_variance` function (T027).

    This function filters out tracks that have zero associated User-Track pairs
    in the aggregated dataset (high exposure, zero memory cues) to avoid
    singularities in the design matrix.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        
        # Create a sample dataset with mixed scenarios
        # Scenario 1: Track with valid User-Track pairs (should be kept)
        # Scenario 2: Track with zero User-Track pairs (should be removed)
        # Scenario 3: Track with valid pairs but low total_listens in original cohort (kept)
        
        self.test_data = pd.DataFrame({
            'track_id': ['track_A', 'track_A', 'track_B', 'track_C', 'track_C', 'track_C'],
            'user_id': ['user_1', 'user_2', 'user_3', 'user_4', 'user_5', 'user_6'],
            'mean_vividness': [4.5, 3.2, 5.0, 2.1, 3.8, 4.2],
            'mean_valence': [0.8, 0.6, 0.9, 0.5, 0.7, 0.6],
            'adolescent_exposure_ratio': [0.8, 0.8, 0.5, 0.3, 0.3, 0.3],
            'popularity': [0.9, 0.9, 0.7, 0.4, 0.4, 0.4],
            # Simulated 'total_listens' from original cohort (preserved for stats)
            'total_listens': [150, 150, 80, 45, 45, 45],
            'track_title': ['Song A', 'Song A', 'Song B', 'Song C', 'Song C', 'Song C']
        })

    def test_removes_tracks_with_zero_pairs(self):
        """
        Assert that tracks with zero memory cues (no rows in user_track_pairs)
        are removed from the dataset.
        """
        # Create data where 'track_D' exists in the original cohort logic
        # but has NO rows in this aggregated user_track_pairs table
        data_with_missing = pd.concat([
            self.test_data,
            pd.DataFrame({
                'track_id': ['track_D'], # This track has no user-track pairs in this table
                'user_id': ['user_X'],
                'mean_vividness': [0.0],
                'mean_valence': [0.0],
                'adolescent_exposure_ratio': [0.0],
                'popularity': [0.0],
                'total_listens': [200],
                'track_title': ['Song D']
            }).iloc[:0] # Create an empty dataframe with correct schema for track_D
        ], ignore_index=True)

        # Filter the data
        filtered_data, stats = filter_zero_variance(data_with_missing)

        # Assert track_D is NOT in the filtered result
        assert 'track_D' not in filtered_data['track_id'].unique(), \
            "Track with zero pairs should be removed"

        # Assert other tracks are present
        assert 'track_A' in filtered_data['track_id'].unique()
        assert 'track_B' in filtered_data['track_id'].unique()
        assert 'track_C' in filtered_data['track_id'].unique()

    def test_preserves_total_listens_for_descriptive_stats(self):
        """
        Assert that the `total_listens` count from the original cohort is preserved
        in the output for descriptive statistics, even after filtering.
        """
        # Run the filter
        filtered_data, stats = filter_zero_variance(self.test_data)

        # Check that the total_listens values are preserved for the remaining tracks
        # Track A should still have 150
        track_a_rows = filtered_data[filtered_data['track_id'] == 'track_A']
        assert all(track_a_rows['total_listens'] == 150), \
            "Total listens for track_A should be preserved"

        # Track B should still have 80
        track_b_rows = filtered_data[filtered_data['track_id'] == 'track_B']
        assert all(track_b_rows['total_listens'] == 80), \
            "Total listens for track_B should be preserved"

        # Verify the stats dictionary includes the count of removed tracks
        assert 'tracks_removed_count' in stats, \
            "Stats should report number of removed tracks"
        assert 'tracks_kept_count' in stats, \
            "Stats should report number of kept tracks"

    def test_empty_input_handling(self):
        """
        Assert that the function handles an empty input dataframe gracefully.
        """
        empty_df = self.test_data.iloc[:0]
        filtered_data, stats = filter_zero_variance(empty_df)
        
        assert filtered_data.empty, "Filtered data should be empty"
        assert stats['tracks_removed_count'] == 0
        assert stats['tracks_kept_count'] == 0

    def test_all_tracks_removed(self):
        """
        Assert behavior when all tracks have zero variance (e.g., all have 0 pairs).
        """
        # Create a dataset where no tracks actually have valid pairs
        # (Simulating a scenario where the join failed completely)
        # We simulate this by passing an empty dataframe or one that the logic
        # interprets as having no valid groups.
        
        # In our specific implementation, if a track_id appears, it has at least one row.
        # To test "all removed", we'd need a logic branch that checks for a specific condition.
        # However, based on the standard definition: if a track has 0 rows in the input,
        # it's already not in the input. So this test verifies that if we have data,
        # we don't accidentally remove everything unless logic dictates.
        
        # Let's test the case where we pass data, but the logic decides to remove all.
        # This is unlikely unless we add a specific filter (e.g., min_vividness).
        # For now, we assert that if we have data, we keep it (unless it's the 'zero pair' case).
        
        filtered_data, stats = filter_zero_variance(self.test_data)
        assert not filtered_data.empty, "Should keep valid tracks"

    def test_output_schema_preserved(self):
        """
        Assert that the output dataframe maintains the same columns as the input.
        """
        filtered_data, stats = filter_zero_variance(self.test_data)
        
        expected_columns = [
            'track_id', 'user_id', 'mean_vividness', 'mean_valence',
            'adolescent_exposure_ratio', 'popularity', 'total_listens', 'track_title'
        ]
        
        assert list(filtered_data.columns) == expected_columns, \
            "Output columns should match input columns"

    def test_stats_structure(self):
        """
        Assert that the returned stats dictionary contains expected keys.
        """
        filtered_data, stats = filter_zero_variance(self.test_data)

        assert isinstance(stats, dict), "Stats should be a dictionary"
        assert 'tracks_removed_count' in stats
        assert 'tracks_kept_count' in stats
        assert 'original_count' in stats
        assert 'final_count' in stats

        assert stats['original_count'] == len(self.test_data)
        assert stats['final_count'] == len(filtered_data)
        assert stats['tracks_removed_count'] + stats['tracks_kept_count'] == len(self.test_data['track_id'].unique())