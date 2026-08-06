"""
Unit tests for Tukey HSD post-hoc analysis functionality.

Tests for code/posthoc_tukey.py
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from posthoc_tukey import (
    load_binned_data,
    run_tukey_hsd,
    save_results
)

class TestLoadBinnedData:
    """Tests for load_binned_data function."""
    
    def test_load_binned_data_success(self, tmp_path):
        """Test successful loading of binned data."""
        # Create test data
        test_data = pd.DataFrame({
            'learner_id': [1, 2, 3, 4, 5],
            'final_grade': [85.5, 90.2, 78.3, 92.1, 88.7],
            'feedback_group': ['Immediate', 'Delayed', 'Immediate', 'Variable', 'Delayed']
        })
        
        # Write to temp file
        input_file = tmp_path / "learners_binned.csv"
        test_data.to_csv(input_file, index=False)
        
        # Mock the DATA_PROCESSED path
        with patch('posthoc_tukey.DATA_PROCESSED', tmp_path):
            result = load_binned_data()
            
            assert len(result) == 5
            assert 'learner_id' in result.columns
            assert 'final_grade' in result.columns
            assert 'feedback_group' in result.columns
            
            # Verify data integrity
            pd.testing.assert_frame_equal(result, test_data)
    
    def test_load_binned_data_missing_file(self, tmp_path):
        """Test error when input file doesn't exist."""
        with patch('posthoc_tukey.DATA_PROCESSED', tmp_path):
            with pytest.raises(FileNotFoundError):
                load_binned_data()
    
    def test_load_binned_data_missing_columns(self, tmp_path):
        """Test error when required columns are missing."""
        # Create test data with missing column
        test_data = pd.DataFrame({
            'learner_id': [1, 2, 3],
            'final_grade': [85.5, 90.2, 78.3]
            # Missing 'feedback_group'
        })
        
        input_file = tmp_path / "learners_binned.csv"
        test_data.to_csv(input_file, index=False)
        
        with patch('posthoc_tukey.DATA_PROCESSED', tmp_path):
            with pytest.raises(ValueError, match="Missing required columns"):
                load_binned_data()

class TestRunTukeyHsd:
    """Tests for run_tukey_hsd function."""
    
    def test_run_tukey_hsd_basic(self):
        """Test basic Tukey HSD execution."""
        # Create test data with clear group differences
        np.random.seed(42)
        test_data = pd.DataFrame({
            'learner_id': list(range(100)),
            'final_grade': np.concatenate([
                np.random.normal(85, 5, 33),  # Immediate
                np.random.normal(80, 5, 33),  # Delayed
                np.random.normal(75, 5, 34)   # Variable
            ]),
            'feedback_group': (
                ['Immediate'] * 33 + 
                ['Delayed'] * 33 + 
                ['Variable'] * 34
            )
        })
        
        results = run_tukey_hsd(test_data)
        
        assert 'results' in results
        assert 'summary' in results
        assert 'significant_pairs' in results
        
        # Check results structure
        assert isinstance(results['results'], pd.DataFrame)
        assert len(results['results']) >= 3  # At least 3 pairwise comparisons for 3 groups
        
        # Check summary structure
        assert results['summary']['total_observations'] == 100
        assert results['summary']['num_groups'] == 3
        assert results['summary']['alpha'] == 0.05
        assert results['summary']['method'] == 'Tukey HSD'
        
        # Check that significant_pairs is a list
        assert isinstance(results['significant_pairs'], list)
    
    def test_run_tukey_hsd_insufficient_data(self):
        """Test error when data is insufficient."""
        test_data = pd.DataFrame({
            'learner_id': [1, 2],
            'final_grade': [85.5, 90.2],
            'feedback_group': ['Immediate', 'Delayed']
        })
        
        # Should fail with insufficient data
        with pytest.raises(ValueError, match="Insufficient data"):
            run_tukey_hsd(test_data)
    
    def test_run_tukey_hsd_single_group(self):
        """Test error when only one group is present."""
        test_data = pd.DataFrame({
            'learner_id': [1, 2, 3, 4, 5],
            'final_grade': [85.5, 90.2, 78.3, 92.1, 88.7],
            'feedback_group': ['Immediate'] * 5
        })
        
        with pytest.raises(ValueError, match="Need at least 2 groups"):
            run_tukey_hsd(test_data)
    
    def test_run_tukey_hsd_with_missing_values(self):
        """Test that missing values are handled correctly."""
        test_data = pd.DataFrame({
            'learner_id': [1, 2, 3, 4, 5],
            'final_grade': [85.5, np.nan, 78.3, 92.1, 88.7],
            'feedback_group': ['Immediate', 'Delayed', 'Immediate', 'Variable', 'Delayed']
        })
        
        # Should not raise error, just filter out NaN
        results = run_tukey_hsd(test_data)
        
        # Should have 4 observations instead of 5
        assert results['summary']['total_observations'] == 4

class TestSaveResults:
    """Tests for save_results function."""
    
    def test_save_results(self, tmp_path):
        """Test saving results to files."""
        # Create mock results
        mock_results_df = pd.DataFrame({
            'Group1': ['Immediate', 'Delayed'],
            'Group2': ['Delayed', 'Variable'],
            'Mean Difference': [5.0, -3.0],
            'Std Err': [1.2, 1.1],
            'Lower CI': [2.5, -5.2],
            'Upper CI': [7.5, -0.8],
            'Reject': [True, False]
        })
        
        mock_summary = {
            'total_observations': 100,
            'num_groups': 3,
            'groups': ['Immediate', 'Delayed', 'Variable'],
            'significant_comparisons': 1,
            'alpha': 0.05,
            'method': 'Tukey HSD'
        }
        
        mock_results = {
            'results': mock_results_df,
            'summary': mock_summary,
            'significant_pairs': [('Immediate', 'Delayed', 5.0)]
        }
        
        # Mock the DATA_PROCESSED path
        with patch('posthoc_tukey.DATA_PROCESSED', tmp_path):
            output_path = save_results(mock_results)
            
            # Check CSV file exists
            assert output_path.exists()
            
            # Check summary JSON exists
            summary_path = tmp_path / "tukey_hsd_summary.json"
            assert summary_path.exists()
            
            # Verify CSV content
            saved_df = pd.read_csv(output_path)
            pd.testing.assert_frame_equal(saved_df, mock_results_df)
            
            # Verify JSON content
            with open(summary_path, 'r') as f:
                saved_summary = json.load(f)
            
            assert saved_summary == mock_summary

class TestIntegration:
    """Integration tests for the full Tukey HSD pipeline."""
    
    def test_full_pipeline(self, tmp_path):
        """Test the complete pipeline from data loading to result saving."""
        # Create test data
        np.random.seed(123)
        test_data = pd.DataFrame({
            'learner_id': list(range(60)),
            'final_grade': np.concatenate([
                np.random.normal(85, 4, 20),
                np.random.normal(80, 4, 20),
                np.random.normal(75, 4, 20)
            ]),
            'feedback_group': (
                ['Immediate'] * 20 +
                ['Delayed'] * 20 +
                ['Variable'] * 20
            )
        })
        
        # Write input file
        input_file = tmp_path / "learners_binned.csv"
        test_data.to_csv(input_file, index=False)
        
        # Mock the DATA_PROCESSED path
        with patch('posthoc_tukey.DATA_PROCESSED', tmp_path):
            # Load data
            df = load_binned_data()
            assert len(df) == 60
            
            # Run Tukey HSD
            results = run_tukey_hsd(df)
            assert results['summary']['total_observations'] == 60
            assert results['summary']['num_groups'] == 3
            
            # Save results
            output_path = save_results(results)
            assert output_path.exists()
            
            # Verify output can be read back
            saved_results = pd.read_csv(output_path)
            assert len(saved_results) == 3  # 3 pairwise comparisons for 3 groups