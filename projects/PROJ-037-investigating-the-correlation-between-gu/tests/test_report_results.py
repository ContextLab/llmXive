"""
Tests for the report_results module.

These tests verify that the results table generation works correctly.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

# Mock the analysis module functions for testing
from unittest.mock import patch, MagicMock

def test_generate_results_table_empty():
    """Test that an empty results DataFrame creates a header-only CSV."""
    from report_results import generate_results_table
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty_results.csv"
        
        # Create an empty DataFrame
        empty_results = pd.DataFrame()
        
        # Generate the table
        generate_results_table(empty_results, output_path)
        
        # Verify the file was created
        assert output_path.exists()
        
        # Read the file and check it has headers
        df = pd.read_csv(output_path)
        # Should have the expected columns even if empty
        expected_columns = ['variable_type', 'variable_name', 'sleep_variable', 'correlation_type', 'effect_size', 'p_value', 'fdr_corrected_p_value', 'sample_size']
        assert list(df.columns) == expected_columns

def test_generate_results_table_with_data():
    """Test that results with data are saved correctly."""
    from report_results import generate_results_table
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "results.csv"
        
        # Create a sample results DataFrame
        sample_data = {
            'variable_type': ['alpha', 'alpha', 'beta'],
            'variable_name': ['Shannon', 'Simpson', 'Bray-Curtis'],
            'sleep_variable': ['duration', 'quality', 'duration'],
            'correlation_type': ['spearman', 'pearson', 'spearman'],
            'effect_size': [0.35, -0.22, 0.18],
            'p_value': [0.01, 0.04, 0.08],
            'fdr_corrected_p_value': [0.03, 0.06, 0.12],
            'sample_size': [150, 150, 150]
        }
        results_df = pd.DataFrame(sample_data)
        
        # Generate the table
        generate_results_table(results_df, output_path)
        
        # Verify the file was created
        assert output_path.exists()
        
        # Read and verify the data
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 3
        assert list(saved_df.columns) == list(results_df.columns)
        
        # Check that data is preserved (order might differ due to sorting)
        assert set(saved_df['variable_name']) == set(results_df['variable_name'])

def test_generate_results_table_sorting():
    """Test that results are sorted by FDR-corrected p-value."""
    from report_results import generate_results_table
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sorted_results.csv"
        
        # Create a sample results DataFrame with unsorted p-values
        sample_data = {
            'variable_type': ['alpha', 'alpha', 'beta'],
            'variable_name': ['Shannon', 'Simpson', 'Bray-Curtis'],
            'sleep_variable': ['duration', 'quality', 'duration'],
            'correlation_type': ['spearman', 'pearson', 'spearman'],
            'effect_size': [0.35, -0.22, 0.18],
            'p_value': [0.01, 0.04, 0.08],
            'fdr_corrected_p_value': [0.12, 0.06, 0.03],  # Unsorted
            'sample_size': [150, 150, 150]
        }
        results_df = pd.DataFrame(sample_data)
        
        # Generate the table
        generate_results_table(results_df, output_path)
        
        # Read and verify sorting
        saved_df = pd.read_csv(output_path)
        
        # Check that fdr_corrected_p_value is sorted in ascending order
        fdr_values = saved_df['fdr_corrected_p_value'].tolist()
        assert fdr_values == sorted(fdr_values), "Results should be sorted by FDR-corrected p-value"

def test_load_correlation_results_integration():
    """Test the integration of load_correlation_results with mocked dependencies."""
    with patch('report_results.load_processed_cohort') as mock_load_cohort, \
         patch('report_results.calculate_alpha_diversity') as mock_alpha, \
         patch('report_results.calculate_beta_diversity') as mock_beta, \
         patch('report_results.run_all_correlations') as mock_run_corr:
        
        from report_results import load_correlation_results
        
        # Setup mocks
        mock_cohort = MagicMock()
        mock_alpha_result = MagicMock()
        mock_beta_result = MagicMock()
        mock_results = pd.DataFrame({'test': [1, 2, 3]})
        
        mock_load_cohort.return_value = mock_cohort
        mock_alpha.return_value = mock_alpha_result
        mock_beta.return_value = mock_beta_result
        mock_run_corr.return_value = mock_results
        
        # Call the function
        results = load_correlation_results()
        
        # Verify the mocks were called correctly
        mock_load_cohort.assert_called_once()
        mock_alpha.assert_called_once_with(mock_cohort)
        mock_beta.assert_called_once_with(mock_cohort)
        mock_run_corr.assert_called_once_with(mock_cohort, mock_alpha_result, mock_beta_result)
        
        # Verify the result
        assert results.equals(mock_results)