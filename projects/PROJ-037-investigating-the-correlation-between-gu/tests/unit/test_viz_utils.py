import pytest
import pandas as pd
import numpy as np
from code.viz import load_correlation_results, load_beta_diversity_data

class TestLoadCorrelationResultsViz:
    def test_load_correlation_results_for_viz(self):
        """Test that load_correlation_results works for visualization."""
        try:
            results = load_correlation_results()
            assert isinstance(results, pd.DataFrame)
            assert len(results) > 0
            # Check for required columns for plotting
            assert 'variable' in results.columns
            assert 'correlation' in results.columns
            assert 'p_value' in results.columns
        except FileNotFoundError:
            pytest.skip("correlation_results.csv not found - expected in development")

class TestLoadBetaDiversityData:
    def test_load_beta_diversity_data_structure(self):
        """Test that load_beta_diversity_data returns expected structure."""
        try:
            data = load_beta_diversity_data()
            assert isinstance(data, pd.DataFrame)
            # Check for expected columns
            assert 'sample_id' in data.columns or 'participant_id' in data.columns
            # Should have distance matrix or coordinates
            assert len(data.columns) > 1
        except FileNotFoundError:
            pytest.skip("beta_diversity data not found - expected in development")

    def test_load_beta_diversity_data_empty(self):
        """Test behavior when beta diversity data is empty."""
        # Create empty dataframe to simulate missing data
        empty_df = pd.DataFrame()
        
        # This would typically raise an error or return empty result
        # The exact behavior depends on implementation
        with pytest.raises((FileNotFoundError, ValueError)):
            load_beta_diversity_data()