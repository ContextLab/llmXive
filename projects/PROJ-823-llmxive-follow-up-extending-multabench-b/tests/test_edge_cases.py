"""
Tests for edge case handling in the MulTaBench pipeline.

Tests cover:
- Zero variance detection and handling
- Missing field detection and handling
- Empty and single-row datasets
- Integration with preprocessing pipeline
"""
import pytest
import pandas as pd
import numpy as np
from code.embeddings.edge_case_handler import (
    EdgeCaseHandler,
    detect_zero_variance_columns,
    detect_missing_fields,
    handle_zero_variance_columns,
    handle_missing_fields,
    preprocess_dataset_for_edge_cases
)

class TestZeroVariance:
    """Tests for zero variance detection and handling."""
    
    def test_detect_zero_variance_constant_column(self):
        """Test detection of a constant column."""
        df = pd.DataFrame({
            'constant': [5.0] * 100,
            'variable': np.random.randn(100)
        })
        
        handler = EdgeCaseHandler()
        result = handler.detect_zero_variance(df)
        
        assert 'constant' in result
        assert 'variable' not in result
    
    def test_detect_zero_variance_all_nan(self):
        """Test detection of all-NaN column as zero variance."""
        df = pd.DataFrame({
            'all_nan': [np.nan] * 100,
            'variable': np.random.randn(100)
        })
        
        handler = EdgeCaseHandler()
        result = handler.detect_zero_variance(df)
        
        assert 'all_nan' in result
    
    def test_handle_zero_variance_skip(self):
        """Test dropping zero variance columns."""
        df = pd.DataFrame({
            'constant': [5.0] * 100,
            'variable': np.random.randn(100)
        })
        
        handler = EdgeCaseHandler(skip_zero_variance=True)
        result_df, metadata = handler.handle_zero_variance(df, ['constant'])
        
        assert 'constant' not in result_df.columns
        assert 'variable' in result_df.columns
        assert metadata['action'] == 'drop'
    
    def test_handle_zero_variance_impute(self):
        """Test imputing zero variance columns with mean."""
        df = pd.DataFrame({
            'constant': [5.0] * 100,
            'variable': np.random.randn(100)
        })
        
        handler = EdgeCaseHandler(skip_zero_variance=False)
        result_df, metadata = handler.handle_zero_variance(df, ['constant'])
        
        assert 'constant' in result_df.columns
        assert result_df['constant'].iloc[0] == 5.0
        assert metadata['action'] == 'impute'

class TestMissingFields:
    """Tests for missing field detection and handling."""
    
    def test_detect_missing_fields(self):
        """Test detection of missing values in required fields."""
        df = pd.DataFrame({
            'required1': [1.0, 2.0, np.nan, 4.0],
            'required2': [10.0, np.nan, 30.0, 40.0],
            'optional': [100.0, 200.0, 300.0, 400.0]
        })
        
        handler = EdgeCaseHandler()
        result = handler.detect_missing_fields(df, ['required1', 'required2'])
        
        assert 'required1' in result
        assert 'required2' in result
        assert result['required1'] == 1
        assert result['required2'] == 1
        assert 'optional' not in result
    
    def test_handle_missing_fields_skip(self):
        """Test dropping rows with missing required fields."""
        df = pd.DataFrame({
            'required1': [1.0, 2.0, np.nan, 4.0],
            'required2': [10.0, 20.0, 30.0, 40.0]
        })
        
        handler = EdgeCaseHandler(missing_strategy='skip')
        result_df, metadata = handler.handle_missing_fields(
            df,
            {'required1': 1},
            ['required1', 'required2']
        )
        
        assert len(result_df) == 3
        assert metadata['action'] == 'skip_rows'
        assert metadata['rows_dropped'] == 1
    
    def test_handle_missing_fields_impute(self):
        """Test imputing missing values in required fields."""
        df = pd.DataFrame({
            'required1': [1.0, 2.0, np.nan, 4.0],
            'required2': [10.0, 20.0, 30.0, 40.0]
        })
        
        handler = EdgeCaseHandler(missing_strategy='impute', impute_value=0.0)
        result_df, metadata = handler.handle_missing_fields(
            df,
            {'required1': 1},
            ['required1', 'required2']
        )
        
        assert len(result_df) == 4
        assert result_df['required1'].iloc[2] == 0.0
        assert metadata['action'] == 'impute'

class TestFullPipeline:
    """Tests for the full edge case handling pipeline."""
    
    def test_process_full_pipeline(self):
        """Test complete processing pipeline."""
        df = pd.DataFrame({
            'constant': [5.0] * 100,
            'required1': np.random.randn(100),
            'required2': [10.0] * 99 + [np.nan],
            'variable': np.random.randn(100)
        })
        
        handler = EdgeCaseHandler(
            skip_zero_variance=True,
            missing_strategy='skip'
        )
        
        result_df, metadata = handler.process(
            df,
            required_fields=['required1', 'required2']
        )
        
        # Check zero variance handling
        assert 'constant' not in result_df.columns
        assert metadata['zero_variance']['action'] == 'drop'
        
        # Check missing field handling
        assert len(result_df) == 99
        assert metadata['missing_fields']['action'] == 'skip_rows'
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        
        handler = EdgeCaseHandler()
        result_df, metadata = handler.process(
            df,
            required_fields=['required1']
        )
        
        assert result_df.empty
        assert metadata['original_shape'] == (0, 0)
        assert metadata['final_shape'] == (0, 0)
    
    def test_single_row_dataset(self):
        """Test handling of single-row dataset."""
        df = pd.DataFrame({
            'required1': [1.0],
            'required2': [2.0]
        })
        
        handler = EdgeCaseHandler()
        result_df, metadata = handler.process(
            df,
            required_fields=['required1', 'required2']
        )
        
        assert len(result_df) == 1
        assert metadata['final_shape'] == (1, 2)

class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_detect_zero_variance_columns_func(self):
        """Test the standalone detect_zero_variance_columns function."""
        df = pd.DataFrame({
            'constant': [5.0] * 100,
            'variable': np.random.randn(100)
        })
        
        result = detect_zero_variance_columns(df)
        assert 'constant' in result
    
    def test_preprocess_dataset_for_edge_cases_func(self):
        """Test the standalone preprocess_dataset_for_edge_cases function."""
        df = pd.DataFrame({
            'constant': [5.0] * 100,
            'required1': np.random.randn(100),
            'required2': [10.0] * 99 + [np.nan]
        })
        
        result_df, metadata = preprocess_dataset_for_edge_cases(
            df,
            required_fields=['required1', 'required2'],
            skip_zero_variance=True,
            missing_strategy='skip'
        )
        
        assert 'constant' not in result_df.columns
        assert len(result_df) == 99
