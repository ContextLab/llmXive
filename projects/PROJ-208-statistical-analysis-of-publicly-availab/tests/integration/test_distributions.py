"""
Integration tests for distribution fitting output format.
"""

import pytest
import json
import numpy as np
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.distribution_fitting import (
    analyze_distributions, 
    generate_ecdf_plot, 
    generate_fit_comparison_plot,
    save_results,
    save_figures
)
import pandas as pd

class TestDistributionFittingIntegration:
    """Integration tests for distribution fitting module."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        data = {
            'resolution_time_hours': np.random.lognormal(mean=3.5, sigma=1.5, size=1000),
            'repo_name': ['repo1'] * 1000
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_analyze_distributions_output_format(self, sample_dataframe):
        """Test that analyze_distributions returns correct output format."""
        results = analyze_distributions(sample_dataframe, 'resolution_time_hours')
        
        # Check top-level keys
        assert 'metadata' in results
        assert 'distributions' in results
        assert 'best_fit' in results
        
        # Check metadata structure
        assert 'total_samples' in results['metadata']
        assert 'positive_samples' in results['metadata']
        assert 'mean_resolution_time' in results['metadata']
        assert 'median_resolution_time' in results['metadata']
        
        # Check distribution results
        assert 'lognorm' in results['distributions']
        assert 'weibull_min' in results['distributions']
        
        # Check individual distribution structure
        for dist_name, dist_result in results['distributions'].items():
            assert 'status' in dist_result
            assert dist_result['status'] == 'success'
            assert 'parameters' in dist_result
            assert 'ks_statistic' in dist_result
            assert 'p_value' in dist_result
            assert 'aic' in dist_result
            assert 'n_samples' in dist_result

    def test_ecdf_plot_generation(self, sample_dataframe):
        """Test ECDF plot generation."""
        data = sample_dataframe['resolution_time_hours'].values
        fig = generate_ecdf_plot(data)
        
        assert fig is not None
        assert len(fig.axes) == 1
        ax = fig.axes[0]
        
        # Check that x-axis is log scale
        assert ax.get_xscale() == 'log'
        
        # Check labels
        assert ax.get_xlabel() == 'Resolution Time (hours)'
        assert ax.get_ylabel() == 'Cumulative Probability'

    def test_fit_comparison_plot_generation(self, sample_dataframe):
        """Test fit comparison plot generation."""
        data = sample_dataframe['resolution_time_hours'].values
        results = analyze_distributions(sample_dataframe, 'resolution_time_hours')
        fig = generate_fit_comparison_plot(data, results)
        
        assert fig is not None
        assert len(fig.axes) == 1
        ax = fig.axes[0]
        
        # Check that x-axis is log scale
        assert ax.get_xscale() == 'log'
        
        # Check legend exists
        assert ax.get_legend() is not None

    def test_save_results_json_format(self, sample_dataframe, temp_output_dir):
        """Test that results are saved in valid JSON format."""
        results = analyze_distributions(sample_dataframe, 'resolution_time_hours')
        output_path = temp_output_dir / 'test_results.json'
        
        save_results(results, output_path)
        
        assert output_path.exists()
        
        # Load and verify JSON
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results

    def test_save_figures(self, sample_dataframe, temp_output_dir):
        """Test that figures are saved as PNG files."""
        data = sample_dataframe['resolution_time_hours'].values
        results = analyze_distributions(sample_dataframe, 'resolution_time_hours')
        
        figs = {
            'ecdf': generate_ecdf_plot(data),
            'fit_comparison': generate_fit_comparison_plot(data, results)
        }
        
        save_figures(figs, temp_output_dir)
        
        # Check that PNG files were created
        assert (temp_output_dir / 'ecdf.png').exists()
        assert (temp_output_dir / 'fit_comparison.png').exists()

    def test_full_pipeline_integration(self, sample_dataframe, temp_output_dir):
        """Test the full distribution fitting pipeline."""
        # Analyze distributions
        results = analyze_distributions(sample_dataframe, 'resolution_time_hours')
        
        # Generate figures
        data = sample_dataframe['resolution_time_hours'].values
        figs = {
            'ecdf': generate_ecdf_plot(data),
            'fit_comparison': generate_fit_comparison_plot(data, results)
        }
        
        # Save outputs
        save_results(results, temp_output_dir / 'results.json')
        save_figures(figs, temp_output_dir)
        
        # Verify all outputs exist
        assert (temp_output_dir / 'results.json').exists()
        assert (temp_output_dir / 'ecdf.png').exists()
        assert (temp_output_dir / 'fit_comparison.png').exists()
        
        # Verify JSON content
        with open(temp_output_dir / 'results.json', 'r') as f:
            saved_results = json.load(f)
        
        assert 'best_fit' in saved_results
        assert saved_results['best_fit'] is not None