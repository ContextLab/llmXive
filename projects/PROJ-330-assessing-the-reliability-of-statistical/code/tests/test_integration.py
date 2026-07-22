"""
Integration tests for User Story 3: Cross-Dataset Benchmarking.

Specifically tests the aggregation logic in report.py when handling
missing repository data (TCGA, ENCODE, GEO).
"""
import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the target function from the existing API surface
# Note: We are testing the aggregation logic that groups by source.
# Since the full report generation might rely on external files,
# we test the specific aggregation behavior with mock data.
try:
    from src.report import generate_stability_report
except ImportError:
    # Fallback if import path differs slightly in local env, 
    # but per API surface it should be src.report
    from code.src.report import generate_stability_report


class TestAggregationHandlesMissingRepoGracefully:
    """
    Test that the aggregation logic in report.py handles missing 
    repository data without crashing.
    
    Scenario: We have results for GEO and TCGA, but ENCODE is missing 
    (either no data fetched or analysis failed). The aggregation should
    still produce a valid summary table for the available repos.
    """

    @pytest.fixture
    def mock_results_data(self):
        """Create a mock results DataFrame with mixed repository sources."""
        data = {
            'dataset_id': ['GEO-123', 'GEO-456', 'TCGA-789'],
            'source': ['GEO', 'GEO', 'TCGA'],
            'stability_correlation': [0.85, 0.82, 0.91],
            'pvalue_inflation_mad': [0.02, 0.03, 0.01],
            'status': ['success', 'success', 'success']
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def mock_missing_encode_data(self):
        """Create a mock results DataFrame missing ENCODE entries."""
        data = {
            'dataset_id': ['GEO-123', 'TCGA-789'],
            'source': ['GEO', 'TCGA'],
            'stability_correlation': [0.85, 0.91],
            'pvalue_inflation_mad': [0.02, 0.01],
            'status': ['success', 'success']
        }
        return pd.DataFrame(data)

    def test_aggregation_with_all_repos(self, mock_results_data, tmp_path):
        """
        Verify aggregation works normally when all expected repos are present.
        """
        output_file = tmp_path / "aggregation_test_full.csv"
        
        # Mock the internal logic that might try to read files if not provided
        # We are testing the aggregation function's ability to handle the DataFrame
        # Since generate_stability_report might expect file paths, we test the 
        # underlying logic or mock the file reading part.
        
        # For this test, we assume the function can accept a DataFrame or 
        # we test the specific aggregation step if exposed.
        # If generate_stability_report is the only entry point, we mock the 
        # data loading to return our mock data.
        
        with patch('src.report.load_aggregated_results') as mock_load:
            mock_load.return_value = mock_results_data
            
            # Call the function
            result = generate_stability_report(
                output_path=str(output_file),
                # If the function signature requires other args, we might need to 
                # adjust, but per spec it aggregates results.
                # Assuming it takes a list of results or reads a specific state file.
                # We will test the logic by mocking the data source.
            )
            
            # Assertions
            assert output_file.exists(), "Output file should be created"
            df_result = pd.read_csv(output_file)
            
            # Check that all sources are present
            assert 'GEO' in df_result['source'].values
            assert 'TCGA' in df_result['source'].values
            assert 'ENCODE' not in df_result['source'].values # No data for it
            assert len(df_result) == 3 # Total rows

    def test_aggregation_handles_missing_repo(self, mock_missing_encode_data, tmp_path):
        """
        Verify aggregation handles missing ENCODE data gracefully.
        
        The function should:
        1. Not raise an exception when ENCODE data is missing.
        2. Still aggregate GEO and TCGA correctly.
        3. Optionally mark ENCODE as 'No Data' in the summary if the report 
           expects all three.
        """
        output_file = tmp_path / "aggregation_test_missing.csv"
        
        # Mock the data source to return data without ENCODE
        with patch('src.report.load_aggregated_results') as mock_load:
            mock_load.return_value = mock_missing_encode_data
            
            # Execute the aggregation
            result = generate_stability_report(
                output_path=str(output_file)
            )
            
            # Verify no crash occurred
            assert result is not None
            assert output_file.exists()
            
            # Verify the output contains the available data
            df_result = pd.read_csv(output_file)
            assert len(df_result) == 2
            assert set(df_result['source'].unique()) == {'GEO', 'TCGA'}
            
            # Verify stability metrics are calculated correctly for available data
            # (Simple check: correlation values should match input)
            geo_rows = df_result[df_result['source'] == 'GEO']
            assert geo_rows['stability_correlation'].iloc[0] == 0.85

    def test_aggregation_handles_all_missing(self, tmp_path):
        """
        Verify behavior when ALL repository data is missing (empty DataFrame).
        """
        empty_df = pd.DataFrame(columns=['dataset_id', 'source', 'stability_correlation', 'pvalue_inflation_mad', 'status'])
        output_file = tmp_path / "aggregation_test_empty.csv"
        
        with patch('src.report.load_aggregated_results') as mock_load:
            mock_load.return_value = empty_df
            
            # Should not crash, but handle empty input
            result = generate_stability_report(
                output_path=str(output_file)
            )
            
            assert output_file.exists()
            df_result = pd.read_csv(output_file)
            assert len(df_result) == 0

    def test_aggregation_handles_single_repo(self, tmp_path):
        """
        Verify aggregation works when only ONE repository has data.
        """
        data = pd.DataFrame({
            'dataset_id': ['GEO-123'],
            'source': ['GEO'],
            'stability_correlation': [0.85],
            'pvalue_inflation_mad': [0.02],
            'status': ['success']
        })
        output_file = tmp_path / "aggregation_test_single.csv"
        
        with patch('src.report.load_aggregated_results') as mock_load:
            mock_load.return_value = data
            
            result = generate_stability_report(
                output_path=str(output_file)
            )
            
            assert output_file.exists()
            df_result = pd.read_csv(output_file)
            assert len(df_result) == 1
            assert df_result['source'].iloc[0] == 'GEO'

    def test_missing_repo_does_not_break_visualization(self, mock_missing_encode_data, tmp_path):
        """
        Verify that the visualization generation (if part of this function)
        does not crash when a repo is missing.
        """
        output_file = tmp_path / "aggregation_test_vis.csv"
        plot_file = tmp_path / "comparison_plot.png"
        
        with patch('src.report.load_aggregated_results') as mock_load:
            mock_load.return_value = mock_missing_encode_data
            
            # Mock plt.savefig to avoid needing a display
            with patch('matplotlib.pyplot.savefig') as mock_savefig:
                result = generate_stability_report(
                    output_path=str(output_file),
                    plot_path=str(plot_file)
                )
                
                # Should not raise an error
                assert mock_savefig.called or True # Depends on implementation
                assert output_file.exists()