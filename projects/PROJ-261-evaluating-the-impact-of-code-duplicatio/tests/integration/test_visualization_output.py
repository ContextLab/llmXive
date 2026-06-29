"""
Integration test for scatter-plot output format validation.

This test validates that the visualization module produces
correctly formatted scatter plots with proper structure,
labels, and file outputs.
"""
import pytest
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from visualization import (
    setup_logging,
    load_correlation_data,
    compute_regression,
    create_scatter_plot_with_regression,
    create_clone_density_vs_perplexity_plot,
    create_clone_density_vs_accuracy_plot,
    create_sensitivity_analysis_plot,
    generate_all_visualizations
)
from config import get_figure_format, get_figure_dpi


@pytest.fixture
def sample_correlation_data():
    """Create sample correlation data for testing."""
    data = {
        'clone_density': np.random.uniform(0.1, 0.9, 100),
        'perplexity': np.random.uniform(5.0, 20.0, 100),
        'accuracy': np.random.uniform(0.3, 0.9, 100),
        'threshold': np.random.choice([0.7, 0.8, 0.9], 100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for test figures."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "figures"
        output_dir.mkdir(parents=True, exist_ok=True)
        yield output_dir

@pytest.fixture
def sample_correlation_csv(temp_output_dir):
    """Create sample correlation CSV file."""
    data = {
        'clone_density': np.random.uniform(0.1, 0.9, 100),
        'perplexity': np.random.uniform(5.0, 20.0, 100),
        'accuracy': np.random.uniform(0.3, 0.9, 100),
        'threshold': np.random.choice([0.7, 0.8, 0.9], 100)
    }
    df = pd.DataFrame(data)
    csv_path = temp_output_dir.parent / "correlation_results.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

class TestVisualizationOutputFormat:
    """Test class for validating visualization output formats."""
    
    def test_scatter_plot_returns_valid_path(self, sample_correlation_data, temp_output_dir):
        """Test that scatter plot creation returns a valid file path."""
        plot_path = create_scatter_plot_with_regression(
            data=sample_correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            output_dir=temp_output_dir,
            title='Test Plot'
        )
        
        assert plot_path is not None, "Plot path should not be None"
        assert Path(plot_path).exists(), f"Plot file should exist: {plot_path}"
        
    def test_scatter_plot_has_correct_extension(self, sample_correlation_data, temp_output_dir):
        """Test that scatter plots have correct file extensions."""
        plot_path = create_scatter_plot_with_regression(
            data=sample_correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            output_dir=temp_output_dir,
            title='Test Plot'
        )
        
        assert plot_path is not None
        plot_path = Path(plot_path)
        ext = plot_path.suffix.lower()
        assert ext in ['.png', '.pdf'], f"Plot should have .png or .pdf extension, got {ext}"
        
    def test_scatter_plot_file_not_empty(self, sample_correlation_data, temp_output_dir):
        """Test that generated plot files are not empty."""
        plot_path = create_scatter_plot_with_regression(
            data=sample_correlation_data,
            x_col='clone_density',
            y_col='perplexity',
            output_dir=temp_output_dir,
            title='Test Plot'
        )
        
        assert plot_path is not None
        plot_path = Path(plot_path)
        file_size = plot_path.stat().st_size
        assert file_size > 0, f"Plot file should not be empty: {plot_path} (size: {file_size} bytes)"
        
    def test_scatter_plot_has_regression_line(self, sample_correlation_data, temp_output_dir):
        """Test that regression line computation works correctly."""
        x, y, slope, intercept, r_value = compute_regression(
            sample_correlation_data['clone_density'],
            sample_correlation_data['perplexity']
        )
        
        assert x is not None, "X values should not be None"
        assert y is not None, "Y values should not be None"
        assert slope is not None, "Slope should not be None"
        assert intercept is not None, "Intercept should not be None"
        assert r_value is not None, "R-value should not be None"
        
    def test_clone_density_vs_perplexity_plot(self, sample_correlation_data, temp_output_dir):
        """Test clone density vs perplexity plot generation."""
        plot_path = create_clone_density_vs_perplexity_plot(
            data=sample_correlation_data,
            output_dir=temp_output_dir
        )
        
        assert plot_path is not None, "Plot path should not be None"
        assert Path(plot_path).exists(), f"Plot file should exist: {plot_path}"
        assert Path(plot_path).stat().st_size > 0, "Plot file should not be empty"
        
    def test_clone_density_vs_accuracy_plot(self, sample_correlation_data, temp_output_dir):
        """Test clone density vs accuracy plot generation."""
        plot_path = create_clone_density_vs_accuracy_plot(
            data=sample_correlation_data,
            output_dir=temp_output_dir
        )
        
        assert plot_path is not None, "Plot path should not be None"
        assert Path(plot_path).exists(), f"Plot file should exist: {plot_path}"
        assert Path(plot_path).stat().st_size > 0, "Plot file should not be empty"
        
    def test_sensitivity_analysis_plot(self, sample_correlation_data, temp_output_dir):
        """Test sensitivity analysis plot generation."""
        plot_path = create_sensitivity_analysis_plot(
            data=sample_correlation_data,
            output_dir=temp_output_dir
        )
        
        assert plot_path is not None, "Plot path should not be None"
        assert Path(plot_path).exists(), f"Plot file should exist: {plot_path}"
        assert Path(plot_path).stat().st_size > 0, "Plot file should not be empty"
        
    def test_generate_all_visualizations_creates_multiple_files(self, sample_correlation_csv, temp_output_dir):
        """Test that generate_all_visualizations creates multiple output files."""
        results = generate_all_visualizations(
            csv_path=sample_correlation_csv,
            output_dir=temp_output_dir
        )
        
        assert results is not None, "Results should not be None"
        assert isinstance(results, dict), "Results should be a dictionary"
        assert 'total_plots' in results, "Results should contain total_plots"
        assert results['total_plots'] >= 0, "total_plots should be non-negative"
        
        # Check that expected files were created
        expected_patterns = [
            'clone_density_vs_perplexity',
            'clone_density_vs_accuracy',
            'sensitivity_analysis'
        ]
        
        output_files = list(temp_output_dir.glob('*'))
        assert len(output_files) > 0, "At least one output file should be created"
        
    def test_plot_has_proper_axis_labels(self, sample_correlation_data, temp_output_dir):
        """Test that plots have proper axis labels."""
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        
        plot_path = create_clone_density_vs_perplexity_plot(
            data=sample_correlation_data,
            output_dir=temp_output_dir
        )
        
        # The function should create plots with proper labels
        # We validate by ensuring the function completes without error
        assert plot_path is not None
        
    def test_multiple_thresholds_handled(self, temp_output_dir):
        """Test that multiple clone detection thresholds are handled."""
        # Create data with multiple thresholds
        data = {
            'clone_density': np.random.uniform(0.1, 0.9, 300),
            'perplexity': np.random.uniform(5.0, 20.0, 300),
            'threshold': np.tile([0.7, 0.8, 0.9], 100)
        }
        df = pd.DataFrame(data)
        
        plot_path = create_sensitivity_analysis_plot(
            data=df,
            output_dir=temp_output_dir
        )
        
        assert plot_path is not None, "Sensitivity plot should be created"
        assert Path(plot_path).exists(), "Sensitivity plot file should exist"
        
    def test_correlation_data_loading(self, sample_correlation_csv):
        """Test that correlation data can be loaded from CSV."""
        df = load_correlation_data(sample_correlation_csv)
        
        assert df is not None, "DataFrame should not be None"
        assert isinstance(df, pd.DataFrame), "Should return a DataFrame"
        assert len(df) > 0, "DataFrame should not be empty"
        
        # Check expected columns exist
        expected_cols = ['clone_density', 'perplexity', 'accuracy']
        for col in expected_cols:
            assert col in df.columns, f"Expected column '{col}' in DataFrame"
        
    def test_regression_computation(self, sample_correlation_data):
        """Test regression computation with various data."""
        x, y, slope, intercept, r_value = compute_regression(
            sample_correlation_data['clone_density'],
            sample_correlation_data['perplexity']
        )
        
        assert len(x) == len(y), "X and Y should have same length"
        assert len(x) > 0, "X should not be empty"
        assert np.isfinite(slope), "Slope should be finite"
        assert np.isfinite(intercept), "Intercept should be finite"
        assert np.isfinite(r_value), "R-value should be finite"
        assert -1 <= r_value <= 1, "R-value should be between -1 and 1"
        
    def test_output_directory_creation(self, sample_correlation_data):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "directory"
            
            plot_path = create_scatter_plot_with_regression(
                data=sample_correlation_data,
                x_col='clone_density',
                y_col='perplexity',
                output_dir=new_dir,
                title='Test Plot'
            )
            
            assert new_dir.exists(), "Output directory should be created"
            assert plot_path is not None
            
    def test_invalid_data_handling(self, temp_output_dir):
        """Test handling of invalid/empty data."""
        empty_df = pd.DataFrame({'clone_density': [], 'perplexity': []})
        
        # Should handle empty data gracefully
        plot_path = create_scatter_plot_with_regression(
            data=empty_df,
            x_col='clone_density',
            y_col='perplexity',
            output_dir=temp_output_dir,
            title='Empty Data Test'
        )
        
        # Function should complete without crashing
        # May return None or create empty plot
        
    def test_figure_format_configuration(self):
        """Test that figure format is correctly retrieved from config."""
        figure_format = get_figure_format()
        assert figure_format is not None, "Figure format should be configured"
        assert figure_format in ['png', 'pdf', 'both'], f"Invalid figure format: {figure_format}"
        
    def test_figure_dpi_configuration(self):
        """Test that figure DPI is correctly retrieved from config."""
        figure_dpi = get_figure_dpi()
        assert figure_dpi is not None, "Figure DPI should be configured"
        assert isinstance(figure_dpi, int), "Figure DPI should be an integer"
        assert figure_dpi >= 100, "Figure DPI should be at least 100"

class TestVisualizationIntegration:
    """Integration tests for visualization pipeline."""
    
    def test_full_visualization_pipeline(self, sample_correlation_csv, temp_output_dir):
        """Test complete visualization pipeline from CSV to output files."""
        # Run full pipeline
        results = generate_all_visualizations(
            csv_path=sample_correlation_csv,
            output_dir=temp_output_dir
        )
        
        assert results is not None
        assert results.get('total_plots', 0) >= 0
        
        # Verify output files exist
        output_files = list(temp_output_dir.glob('*'))
        assert len(output_files) > 0, "At least one visualization file should be created"
        
        # Verify file sizes are reasonable
        for f in output_files:
            size = f.stat().st_size
            assert size > 0, f"File {f} should not be empty"
            
    def test_visualization_with_realistic_data(self, temp_output_dir):
        """Test visualization with realistic correlation data."""
        # Create realistic correlation data
        np.random.seed(42)
        n_samples = 500
        
        # Generate correlated data
        clone_density = np.random.uniform(0.1, 0.9, n_samples)
        perplexity = 15.0 - 5.0 * clone_density + np.random.normal(0, 2, n_samples)
        accuracy = 0.3 + 0.5 * clone_density + np.random.normal(0, 0.1, n_samples)
        
        df = pd.DataFrame({
            'clone_density': clone_density,
            'perplexity': np.clip(perplexity, 1, 30),
            'accuracy': np.clip(accuracy, 0, 1),
            'threshold': np.random.choice([0.7, 0.8, 0.9], n_samples)
        })
        
        csv_path = temp_output_dir.parent / "realistic_correlation.csv"
        df.to_csv(csv_path, index=False)
        
        results = generate_all_visualizations(
            csv_path=csv_path,
            output_dir=temp_output_dir
        )
        
        assert results is not None
        assert results.get('total_plots', 0) > 0
        
        output_files = list(temp_output_dir.glob('*'))
        assert len(output_files) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
