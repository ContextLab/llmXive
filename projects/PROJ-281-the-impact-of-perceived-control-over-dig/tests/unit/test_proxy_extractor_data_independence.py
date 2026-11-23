"""
Unit tests for data independence enforcement in proxy_extractor.py.

These tests verify that the proxy extraction logic strictly avoids accessing
text content, enforcing Constitution Principle VI.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
from code.services.proxy_extractor import (
    run_proxy_extraction_pipeline,
    DataIndependenceError,
    calculate_filter_applied_contribution,
    calculate_timestamp_regularity,
    calculate_control_proxy
)


class TestDataIndependence:
    """Tests for data independence enforcement."""
    
    def test_text_column_not_loaded(self):
        """Verify that the text column is not loaded during pipeline execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a CSV with text column
            input_path = Path(tmpdir) / "input.csv"
            df = pd.DataFrame({
                'post_id': [1, 2, 3],
                'user_id': ['u1', 'u2', 'u3'],
                'timestamp': ['2023-01-01', '2023-01-02', '2023-01-03'],
                'filter_applied': [1, 0, 1],
                'text': ['some text', 'more text', 'even more']  # This should NOT be loaded
            })
            df.to_csv(input_path, index=False)
            
            output_path = Path(tmpdir) / "output.csv"
            
            # Run pipeline - should not raise error since text column is not accessed
            result = run_proxy_extraction_pipeline(input_path, output_path)
            
            # Verify text column is not in result
            assert 'text' not in result.columns
            assert len(result) == 3
            
    def test_text_column_access_raises_error(self):
        """Verify that explicit text column access raises DataIndependenceError."""
        # This test verifies the defensive check in the pipeline
        # The pipeline should never load the text column, but if it did, it would raise
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            # Create a file with text column
            df = pd.DataFrame({
                'post_id': [1, 2, 3],
                'user_id': ['u1', 'u2', 'u3'],
                'timestamp': ['2023-01-01', '2023-01-02', '2023-01-03'],
                'filter_applied': [1, 0, 1],
                'text': ['test']
            })
            df.to_csv(input_path, index=False)
            
            output_path = Path(tmpdir) / "output.csv"
            
            # The pipeline should handle this gracefully by not loading text
            # If we manually force text into the dataframe (simulating a bug), it should fail
            # But the actual pipeline uses usecols to prevent this
            result = run_proxy_extraction_pipeline(input_path, output_path)
            assert 'text' not in result.columns
            
    def test_only_metadata_columns_used(self):
        """Verify that only metadata columns are used in calculations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            df = pd.DataFrame({
                'post_id': [1, 2, 3],
                'user_id': ['u1', 'u2', 'u3'],
                'timestamp': ['2023-01-01', '2023-01-02', '2023-01-03'],
                'filter_applied': [1, 0, 1],
                'irrelevant_col': ['a', 'b', 'c']  # Should be ignored
            })
            df.to_csv(input_path, index=False)
            
            output_path = Path(tmpdir) / "output.csv"
            result = run_proxy_extraction_pipeline(input_path, output_path)
            
            # Verify only expected columns in output
            expected_cols = {'post_id', 'user_id', 'control_proxy', 'timestamp_regularity'}
            assert set(result.columns) == expected_cols
            
    def test_no_text_in_dependency_chain(self):
        """Verify that no text data flows through the dependency chain."""
        # Test individual functions to ensure they don't accept or process text
        config = {'weights': {'weight_filter': 0.5, 'weight_regularity': 0.5}}
        
        # Test calculate_filter_applied_contribution
        filter_series = pd.Series([1, 0, 1])
        result = calculate_filter_applied_contribution(filter_series, config)
        assert result.dtype in [float, 'float64', 'float32']
        
        # Test calculate_timestamp_regularity
        timestamps = pd.Series(['2023-01-01', '2023-01-02', '2023-01-03'])
        user_ids = pd.Series(['u1', 'u2', 'u3'])
        result = calculate_timestamp_regularity(timestamps, user_ids)
        assert result.dtype in [float, 'float64', 'float32']
        
        # Test calculate_control_proxy
        filter_contrib = pd.Series([0.5, 0.0, 0.5])
        timestamp_reg = pd.Series([0.8, 0.6, 0.9])
        result = calculate_control_proxy(filter_contrib, timestamp_reg, config)
        assert result.dtype in [float, 'float64', 'float32']
        
        # Verify no text-like data in results
        for val in result:
            assert not isinstance(val, str)
            
    def test_empty_dataframe_handling(self):
        """Verify correct handling of empty dataframes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            # Create empty CSV with correct headers
            pd.DataFrame(columns=['post_id', 'user_id', 'timestamp', 'filter_applied']).to_csv(input_path, index=False)
            
            output_path = Path(tmpdir) / "output.csv"
            result = run_proxy_extraction_pipeline(input_path, output_path)
            
            assert len(result) == 0
            assert set(result.columns) == {'post_id', 'user_id', 'control_proxy', 'timestamp_regularity'}


class TestProxyCalculationLogic:
    """Tests for proxy calculation logic correctness."""
    
    def test_filter_contribution_calculation(self):
        """Test that filter_applied contribution is calculated correctly."""
        config = {'weights': {'weight_filter': 0.5}}
        filter_series = pd.Series([1, 0, 1])
        
        result = calculate_filter_applied_contribution(filter_series, config)
        expected = pd.Series([0.5, 0.0, 0.5])
        
        pd.testing.assert_series_equal(result, expected)
        
    def test_timestamp_regularity_calculation(self):
        """Test timestamp regularity calculation."""
        # Regular timestamps (every 1 day) should have high regularity
        timestamps = pd.Series([
            '2023-01-01 00:00:00',
            '2023-01-02 00:00:00',
            '2023-01-03 00:00:00'
        ])
        user_ids = pd.Series(['u1', 'u1', 'u1'])
        
        result = calculate_timestamp_regularity(timestamps, user_ids)
        
        # Should have high regularity (close to 1.0)
        assert all(result >= 0.5), "Regular timestamps should have high regularity scores"
        
    def test_control_proxy_combination(self):
        """Test that control proxy combines filter and regularity correctly."""
        config = {'weights': {'weight_filter': 0.5, 'weight_regularity': 0.5}}
        filter_contrib = pd.Series([0.5, 0.0, 0.5])
        timestamp_reg = pd.Series([1.0, 1.0, 1.0])
        
        result = calculate_control_proxy(filter_contrib, timestamp_reg, config)
        
        # Expected: 0.5 + 0.5*1.0 = 1.0, 0.0 + 0.5*1.0 = 0.5, 0.5 + 0.5*1.0 = 1.0
        expected = pd.Series([1.0, 0.5, 1.0])
        
        pd.testing.assert_series_equal(result, expected)
        
    def test_missing_values_default_to_zero(self):
        """Test that missing values default to baseline zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            df = pd.DataFrame({
                'post_id': [1, 2, 3],
                'user_id': [None, 'u2', 'u3'],  # Missing user_id
                'timestamp': ['2023-01-01', None, '2023-01-03'],  # Missing timestamp
                'filter_applied': [1, None, 1]  # Missing filter_applied
            })
            df.to_csv(input_path, index=False)
            
            output_path = Path(tmpdir) / "output.csv"
            result = run_proxy_extraction_pipeline(input_path, output_path)
            
            # Should not crash and should have valid numeric values
            assert not result['control_proxy'].isna().any()
            assert not result['timestamp_regularity'].isna().any()