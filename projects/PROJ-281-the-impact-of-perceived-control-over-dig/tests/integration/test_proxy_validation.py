"""
Integration test for proxy extraction pipeline.

Verifies that:
1. The proxy extractor correctly processes a subset of posts
2. Control proxy values are calculated correctly based on metadata
3. No text data is accessed during proxy calculation
4. The output file exists and contains expected columns
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.services.proxy_extractor import (
    calculate_filter_applied_contribution,
    calculate_timestamp_regularity,
    calculate_control_proxy,
    run_proxy_extraction_pipeline
)
from code.config import CONFIG


class TestProxyValidation:
    """Integration tests for proxy extraction validation."""

    @pytest.fixture
    def sample_metadata_df(self):
        """Create a sample DataFrame with only metadata (no text)."""
        data = {
            'post_id': [1, 2, 3, 4, 5, 6, 7, 8],
            'user_id': ['user_a', 'user_a', 'user_a', 'user_b', 'user_b', 'user_c', 'user_c', 'user_c'],
            'timestamp': [
                '2023-01-01 10:00:00',
                '2023-01-01 11:00:00',
                '2023-01-01 12:00:00',
                '2023-01-02 08:00:00',
                '2023-01-02 09:00:00',
                '2023-01-03 14:00:00',
                '2023-01-03 15:30:00',
                '2023-01-03 17:00:00'
            ],
            'filter_applied': [True, False, True, False, False, True, False, True],
            # Note: NO 'text' column to ensure independence
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_filter_applied_contribution_true(self):
        """Test that filter_applied=True returns 1.0."""
        row = pd.Series({'filter_applied': True})
        assert calculate_filter_applied_contribution(row) == 1.0

    def test_filter_applied_contribution_false(self):
        """Test that filter_applied=False returns 0.0."""
        row = pd.Series({'filter_applied': False})
        assert calculate_filter_applied_contribution(row) == 0.0

    def test_filter_applied_contribution_missing(self):
        """Test that missing filter_applied defaults to 0.0."""
        row = pd.Series({})
        assert calculate_filter_applied_contribution(row) == 0.0

    def test_timestamp_regularity_perfect(self):
        """Test perfect regularity (equal intervals)."""
        timestamps = [
            '2023-01-01 10:00:00',
            '2023-01-01 11:00:00',
            '2023-01-01 12:00:00',
            '2023-01-01 13:00:00'
        ]
        regularity = calculate_timestamp_regularity(timestamps)
        # Perfect regularity should be close to 1.0
        assert regularity > 0.9

    def test_timestamp_regularity_irregular(self):
        """Test irregular timestamps."""
        timestamps = [
            '2023-01-01 10:00:00',
            '2023-01-01 10:05:00',
            '2023-01-01 14:00:00',
            '2023-01-01 14:01:00'
        ]
        regularity = calculate_timestamp_regularity(timestamps)
        # Irregular should be lower
        assert regularity < 0.9

    def test_timestamp_regularity_single_post(self):
        """Test regularity for a single post (should be 0.0)."""
        timestamps = ['2023-01-01 10:00:00']
        regularity = calculate_timestamp_regularity(timestamps)
        assert regularity == 0.0

    def test_timestamp_regularity_empty(self):
        """Test regularity for empty list (should be 0.0)."""
        regularity = calculate_timestamp_regularity([])
        assert regularity == 0.0

    def test_control_proxy_calculation(self):
        """Test full control proxy calculation."""
        row = pd.Series({'filter_applied': True})
        regularity = 1.0  # Perfect regularity
        proxy = calculate_control_proxy(row, regularity)
        # Expected: (1.0 * 0.5) + (1.0 * 0.5) = 1.0
        assert proxy == 1.0

        row = pd.Series({'filter_applied': False})
        proxy = calculate_control_proxy(row, 0.0)
        # Expected: (0.0 * 0.5) + (0.0 * 0.5) = 0.0
        assert proxy == 0.0

    def test_no_text_access_in_proxy_calculation(self):
        """
        Verify that proxy calculation does not access text content.
        
        This test creates a row with a 'text' column but ensures the
        calculation functions ignore it.
        """
        row = pd.Series({
            'filter_applied': True,
            'text': 'This is a test post with anxiety content that should be ignored'
        })
        
        # The function should only look at filter_applied
        proxy = calculate_control_proxy(row, 1.0)
        
        # If it worked correctly, proxy should be 1.0 (filter=True, regularity=1.0)
        assert proxy == 1.0

    def test_full_pipeline_integration(self, sample_metadata_df, temp_output_dir):
        """
        End-to-end test of the proxy extraction pipeline.
        
        Verifies:
        1. Pipeline runs without error
        2. Output file is created
        3. Output has correct columns
        4. Values are within expected range
        """
        input_path = temp_output_dir / 'input.csv'
        output_path = temp_output_dir / 'output.csv'
        
        # Save sample data
        sample_metadata_df.to_csv(input_path, index=False)
        
        # Run pipeline
        stats = run_proxy_extraction_pipeline(input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "Output file was not created"
        
        # Verify output columns
        result_df = pd.read_csv(output_path)
        expected_cols = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
        assert all(col in result_df.columns for col in expected_cols), \
            f"Missing columns. Expected: {expected_cols}, Got: {list(result_df.columns)}"
        
        # Verify row count matches
        assert len(result_df) == len(sample_metadata_df), \
            f"Row count mismatch: {len(result_df)} vs {len(sample_metadata_df)}"
        
        # Verify control_proxy range
        assert result_df['control_proxy'].min() >= 0.0
        assert result_df['control_proxy'].max() <= 1.0
        
        # Verify stats
        assert stats['total_rows'] == len(sample_metadata_df)
        assert stats['output_rows'] == len(sample_metadata_df)
        assert 'avg_control_proxy' in stats

    def test_manual_verification_sample(self, sample_metadata_df, temp_output_dir):
        """
        Manual verification test for a known subset of posts.
        
        Creates a small, deterministic dataset where we can manually
        verify the expected control_proxy values.
        """
        # Create a simple test case
        test_data = {
            'post_id': [100, 101],
            'user_id': ['test_user', 'test_user'],
            'timestamp': [
                '2023-01-01 10:00:00',
                '2023-01-01 11:00:00'  # Perfect 1-hour interval
            ],
            'filter_applied': [True, False]
        }
        test_df = pd.DataFrame(test_data)
        
        input_path = temp_output_dir / 'test_input.csv'
        output_path = temp_output_dir / 'test_output.csv'
        
        test_df.to_csv(input_path, index=False)
        run_proxy_extraction_pipeline(input_path, output_path)
        
        result_df = pd.read_csv(output_path)
        
        # User 'test_user' has perfect regularity (1-hour intervals)
        # Post 100: filter=True (1.0) + regularity=1.0 -> proxy = 0.5*1 + 0.5*1 = 1.0
        # Post 101: filter=False (0.0) + regularity=1.0 -> proxy = 0.5*0 + 0.5*1 = 0.5
        
        post_100 = result_df[result_df['post_id'] == 100].iloc[0]
        post_101 = result_df[result_df['post_id'] == 101].iloc[0]
        
        # Allow small floating point tolerance
        assert abs(post_100['control_proxy'] - 1.0) < 0.01, \
            f"Expected ~1.0 for post 100, got {post_100['control_proxy']}"
        assert abs(post_101['control_proxy'] - 0.5) < 0.01, \
            f"Expected ~0.5 for post 101, got {post_101['control_proxy']}"
        
        # Verify timestamp_regularity is consistent for the same user
        assert post_100['timestamp_regularity'] == post_101['timestamp_regularity']

    def test_missing_metadata_fields(self, temp_output_dir):
        """Test handling of missing metadata fields (should default to 0.0)."""
        # Create data with missing 'filter_applied'
        test_data = {
            'post_id': [1],
            'user_id': ['user_x'],
            'timestamp': ['2023-01-01 10:00:00']
            # No 'filter_applied' column
        }
        test_df = pd.DataFrame(test_data)
        
        input_path = temp_output_dir / 'missing_input.csv'
        output_path = temp_output_dir / 'missing_output.csv'
        
        test_df.to_csv(input_path, index=False)
        
        # Should not raise an error
        stats = run_proxy_extraction_pipeline(input_path, output_path)
        
        result_df = pd.read_csv(output_path)
        assert len(result_df) == 1
        # Missing filter_applied should default to 0.0 contribution
        assert result_df['control_proxy'].iloc[0] >= 0.0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])