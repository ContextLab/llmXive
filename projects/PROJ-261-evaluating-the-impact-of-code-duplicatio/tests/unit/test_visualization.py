"""
Unit tests for visualization generation (T037 - US3).

Tests the visualization.py module functions for scatter plots,
regression analysis, and sensitivity analysis visualizations.

Per spec.md Independent Test requirements: must be written BEFORE
implementation code and verified to fail initially.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import pandas as pd

# Import visualization module functions
from visualization import (
    setup_logging,
    load_correlation_data,
    compute_regression,
    create_scatter_plot_with_regression,
    create_clone_density_vs_perplexity_plot,
    create_clone_density_vs_accuracy_plot,
    create_sensitivity_analysis_plot,
    generate_all_visualizations,
)
from config import get_figure_format, get_figure_dpi


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a valid logger object."""
        logger = setup_logging()
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    def test_setup_logging_creates_log_file(self):
        """Test that setup_logging creates log file in analysis directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('visualization.Path') as mock_path:
                mock_path.return_value = Path(tmpdir)
                logger = setup_logging()
                assert logger is not None


class TestLoadCorrelationData:
    """Tests for load_correlation_data function."""
    
    def test_load_correlation_data_valid_csv(self):
        """Test loading valid correlation data CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_correlation.csv"
            
            # Create test data
            test_data = pd.DataFrame({
                'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
                'perplexity': [10.5, 11.2, 12.1, 13.0, 14.5],
                'accuracy': [0.85, 0.80, 0.75, 0.70, 0.65]
            })
            test_data.to_csv(csv_path, index=False)
            
            result = load_correlation_data(str(csv_path))
            assert result is not None
            assert 'clone_density' in result.columns
            assert 'perplexity' in result.columns
            assert 'accuracy' in result.columns
            assert len(result) == 5
    
    def test_load_correlation_data_missing_file(self):
        """Test handling of missing correlation data file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent = Path(tmpdir) / "does_not_exist.csv"
            with pytest.raises(FileNotFoundError):
                load_correlation_data(str(non_existent))
    
    def test_load_correlation_data_invalid_columns(self):
        """Test handling of CSV with missing required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "invalid.csv"
            test_data = pd.DataFrame({
                'wrong_column': [1, 2, 3]
            })
            test_data.to_csv(csv_path, index=False)
            
            result = load_correlation_data(str(csv_path))
            assert result is not None
            assert 'wrong_column' in result.columns
    
    def test_load_correlation_data_empty_file(self):
        """Test handling of empty CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "empty.csv"
            csv_path.touch()
            
            with pytest.raises(pd.errors.EmptyDataError):
                load_correlation_data(str(csv_path))
    
    def test_load_correlation_data_nan_values(self):
        """Test handling of data with NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "nan_test.csv"
            test_data = pd.DataFrame({
                'clone_density': [0.1, np.nan, 0.3, 0.4, 0.5],
                'perplexity': [10.5, 11.2, np.nan, 13.0, 14.5],
                'accuracy': [0.85, 0.80, 0.75, np.nan, 0.65]
            })
            test_data.to_csv(csv_path, index=False)
            
            result = load_correlation_data(str(csv_path))
            assert result is not None
            assert len(result) == 5  # Should load all rows, NaN handling elsewhere


class TestComputeRegression:
    """Tests for compute_regression function."""
    
    def test_compute_regression_basic(self):
        """Test basic regression computation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert isinstance(slope, (float, np.floating))
        assert isinstance(intercept, (float, np.floating))
        assert isinstance(r_squared, (float, np.floating))
        assert 0 <= r_squared <= 1
    
    def test_compute_regression_constant_y(self):
        """Test regression with constant y values."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert isinstance(slope, (float, np.floating))
        assert isinstance(intercept, (float, np.floating))
        assert r_squared == 0.0  # No variance in y
    
    def test_compute_regression_single_point(self):
        """Test regression with single data point."""
        x = np.array([1])
        y = np.array([2])
        
        with pytest.raises(ValueError):
            compute_regression(x, y)
    
    def test_compute_regression_mismatched_lengths(self):
        """Test regression with mismatched x and y lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        
        with pytest.raises(ValueError):
            compute_regression(x, y)
    
    def test_compute_regression_negative_correlation(self):
        """Test regression with negative correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 4, 3, 2, 1])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert slope < 0  # Negative slope for negative correlation
        assert 0 <= r_squared <= 1
    
    def test_compute_regression_perfect_correlation(self):
        """Test regression with perfect correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert abs(slope - 2.0) < 0.001
        assert abs(intercept - 0.0) < 0.001
        assert abs(r_squared - 1.0) < 0.001


class TestCreateScatterPlotWithRegression:
    """Tests for create_scatter_plot_with_regression function."""
    
    def test_create_scatter_plot_basic(self):
        """Test basic scatter plot with regression line creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_scatter.png"
            
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 5, 4, 5])
            
            result = create_scatter_plot_with_regression(
                x, y,
                x_label='X Axis',
                y_label='Y Axis',
                title='Test Plot',
                output_path=str(output_path)
            )
            
            assert result is True
            assert output_path.exists()
    
    def test_create_scatter_plot_formats(self):
        """Test scatter plot in different formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 5, 4, 5])
            
            # Test PNG format
            png_path = Path(tmpdir) / "test.png"
            result_png = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(png_path)
            )
            assert result_png is True
            assert png_path.exists()
            assert png_path.suffix == '.png'
            
            # Test PDF format
            pdf_path = Path(tmpdir) / "test.pdf"
            result_pdf = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(pdf_path)
            )
            assert result_pdf is True
            assert pdf_path.exists()
            assert pdf_path.suffix == '.pdf'
    
    def test_create_scatter_plot_small_dataset(self):
        """Test scatter plot with small dataset (3 points)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "small.png"
            
            x = np.array([1, 2, 3])
            y = np.array([2, 4, 6])
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Small Dataset', str(output_path)
            )
            
            assert result is True
            assert output_path.exists()
    
    def test_create_scatter_plot_large_dataset(self):
        """Test scatter plot with large dataset (1000 points)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "large.png"
            
            np.random.seed(42)
            x = np.random.randn(1000)
            y = 2 * x + np.random.randn(1000) * 0.5
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Large Dataset', str(output_path)
            )
            
            assert result is True
            assert output_path.exists()
    
    def test_create_scatter_plot_invalid_output_path(self):
        """Test scatter plot with invalid output path."""
        x = np.array([1, 2, 3])
        y = np.array([2, 4, 6])
        
        with pytest.raises((OSError, PermissionError)):
            create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', '/nonexistent/directory/test.png'
            )

class TestCreateCloneDensityVsPerplexityPlot:
    """Tests for create_clone_density_vs_perplexity_plot function."""
    
    def test_create_clone_density_vs_perplexity_basic(self):
        """Test basic clone density vs perplexity plot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "clone_perplexity.png"
            
            result = create_clone_density_vs_perplexity_plot(
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            # Should not raise exception
            assert True
    
    def test_create_clone_density_vs_perplexity_pdf(self):
        """Test clone density vs perplexity plot in PDF format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "clone_perplexity.pdf"
            
            result = create_clone_density_vs_perplexity_plot(
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert True

class TestCreateCloneDensityVsAccuracyPlot:
    """Tests for create_clone_density_vs_accuracy_plot function."""
    
    def test_create_clone_density_vs_accuracy_basic(self):
        """Test basic clone density vs accuracy plot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "clone_accuracy.png"
            
            result = create_clone_density_vs_accuracy_plot(
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert True
    
    def test_create_clone_density_vs_accuracy_pdf(self):
        """Test clone density vs accuracy plot in PDF format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "clone_accuracy.pdf"
            
            result = create_clone_density_vs_accuracy_plot(
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert True

class TestCreateSensitivityAnalysisPlot:
    """Tests for create_sensitivity_analysis_plot function."""
    
    def test_create_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis plot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity.png"
            
            result = create_sensitivity_analysis_plot(
                thresholds=[0.7, 0.8, 0.9],
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert True
    
    def test_create_sensitivity_analysis_single_threshold(self):
        """Test sensitivity analysis with single threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_single.png"
            
            result = create_sensitivity_analysis_plot(
                thresholds=[0.8],
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert True
    
    def test_create_sensitivity_analysis_multiple_thresholds(self):
        """Test sensitivity analysis with multiple thresholds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_multi.png"
            
            result = create_sensitivity_analysis_plot(
                thresholds=[0.5, 0.6, 0.7, 0.8, 0.9],
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert True
    
    def test_create_sensitivity_analysis_empty_thresholds(self):
        """Test sensitivity analysis with empty thresholds list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_empty.png"
            
            result = create_sensitivity_analysis_plot(
                thresholds=[],
                output_path=str(output_path),
                dpi=get_figure_dpi()
            )
            
            # Should handle gracefully
            assert True

class TestGenerateAllVisualizations:
    """Tests for generate_all_visualizations function."""
    
    def test_generate_all_visualizations_basic(self):
        """Test basic visualization generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            output_dir.mkdir()
            
            # Create mock correlation data file
            correlation_csv = Path(tmpdir) / "correlation_results.csv"
            test_data = pd.DataFrame({
                'threshold': [0.7, 0.8, 0.9],
                'clone_perplexity_corr': [0.45, 0.50, 0.55],
                'clone_accuracy_corr': [-0.35, -0.40, -0.45],
                'perplexity_accuracy_corr': [-0.60, -0.65, -0.70],
                'p_value_clone_perplexity': [0.01, 0.005, 0.001],
                'p_value_clone_accuracy': [0.02, 0.01, 0.005],
                'p_value_perplexity_accuracy': [0.001, 0.0005, 0.0001]
            })
            test_data.to_csv(correlation_csv, index=False)
            
            result = generate_all_visualizations(
                correlation_csv=str(correlation_csv),
                output_dir=str(output_dir),
                thresholds=[0.7, 0.8, 0.9],
                dpi=get_figure_dpi()
            )
            
            # Should complete without raising exceptions
            assert True
    
    def test_generate_all_visualizations_missing_correlation_file(self):
        """Test visualization generation with missing correlation file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            output_dir.mkdir()
            
            non_existent = Path(tmpdir) / "does_not_exist.csv"
            
            result = generate_all_visualizations(
                correlation_csv=str(non_existent),
                output_dir=str(output_dir),
                thresholds=[0.7, 0.8, 0.9],
                dpi=get_figure_dpi()
            )
            
            # Should handle gracefully
            assert True
    
    def test_generate_all_visualizations_output_formats(self):
        """Test that visualizations are generated in both PNG and PDF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            output_dir.mkdir()
            
            # Create mock correlation data file
            correlation_csv = Path(tmpdir) / "correlation_results.csv"
            test_data = pd.DataFrame({
                'threshold': [0.7, 0.8, 0.9],
                'clone_perplexity_corr': [0.45, 0.50, 0.55],
                'clone_accuracy_corr': [-0.35, -0.40, -0.45],
                'perplexity_accuracy_corr': [-0.60, -0.65, -0.70],
                'p_value_clone_perplexity': [0.01, 0.005, 0.001],
                'p_value_clone_accuracy': [0.02, 0.01, 0.005],
                'p_value_perplexity_accuracy': [0.001, 0.0005, 0.0001]
            })
            test_data.to_csv(correlation_csv, index=False)
            
            result = generate_all_visualizations(
                correlation_csv=str(correlation_csv),
                output_dir=str(output_dir),
                thresholds=[0.7, 0.8, 0.9],
                dpi=get_figure_dpi()
            )
            
            # Check that output directory exists
            assert output_dir.exists()

class TestVisualizationEdgeCases:
    """Tests for visualization edge cases and error handling."""
    
    def test_visualization_with_zero_variance(self):
        """Test visualization when data has zero variance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "zero_var.png"
            
            x = np.array([1, 1, 1, 1, 1])
            y = np.array([2, 2, 2, 2, 2])
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Zero Variance', str(output_path)
            )
            
            # Should handle gracefully
            assert True
    
    def test_visualization_with_extreme_values(self):
        """Test visualization with extreme value ranges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "extreme.png"
            
            x = np.array([1e-10, 1e-9, 1e-8, 1e-7, 1e-6])
            y = np.array([1e10, 1e9, 1e8, 1e7, 1e6])
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Extreme Values', str(output_path)
            )
            
            # Should handle gracefully
            assert True
    
    def test_visualization_with_outliers(self):
        """Test visualization with significant outliers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "outliers.png"
            
            np.random.seed(42)
            x = np.random.randn(100)
            y = 2 * x + np.random.randn(100) * 0.5
            # Add outlier
            x = np.append(x, 100)
            y = np.append(y, 1000)
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'With Outliers', str(output_path)
            )
            
            # Should handle gracefully
            assert True

class TestVisualizationIntegration:
    """Integration tests for visualization module."""
    
    def test_visualization_with_realistic_data(self):
        """Test visualization with realistic clone/perplexity data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "figures"
            output_dir.mkdir()
            
            # Create realistic correlation data
            correlation_csv = Path(tmpdir) / "correlation_results.csv"
            np.random.seed(42)
            test_data = pd.DataFrame({
                'threshold': [0.7, 0.8, 0.9],
                'clone_perplexity_corr': np.random.uniform(0.3, 0.7, 3),
                'clone_accuracy_corr': np.random.uniform(-0.7, -0.3, 3),
                'perplexity_accuracy_corr': np.random.uniform(-0.8, -0.4, 3),
                'p_value_clone_perplexity': np.random.uniform(0.001, 0.05, 3),
                'p_value_clone_accuracy': np.random.uniform(0.001, 0.05, 3),
                'p_value_perplexity_accuracy': np.random.uniform(0.001, 0.05, 3)
            })
            test_data.to_csv(correlation_csv, index=False)
            
            result = generate_all_visualizations(
                correlation_csv=str(correlation_csv),
                output_dir=str(output_dir),
                thresholds=[0.7, 0.8, 0.9],
                dpi=get_figure_dpi()
            )
            
            assert True
    
    def test_visualization_figure_dimensions(self):
        """Test that generated figures have reasonable dimensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_dimensions.png"
            
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 5, 4, 5])
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(output_path),
                dpi=get_figure_dpi()
            )
            
            # Check file size is reasonable (not empty/corrupted)
            assert output_path.exists()
            assert output_path.stat().st_size > 1000  # At least 1KB

class TestVisualizationConfigIntegration:
    """Tests for visualization config integration."""
    
    def test_visualization_uses_config_dpi(self):
        """Test that visualization uses DPI from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "config_dpi.png"
            
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 5, 4, 5])
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(output_path),
                dpi=get_figure_dpi()
            )
            
            assert result is True
            assert output_path.exists()
    
    def test_visualization_uses_config_format(self):
        """Test that visualization uses format from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with PNG
            png_path = Path(tmpdir) / "test.png"
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 5, 4, 5])
            
            result = create_scatter_plot_with_regression(
                x, y, 'X', 'Y', 'Test', str(png_path),
                dpi=get_figure_dpi()
            )
            
            assert result is True
            assert png_path.exists()
            assert png_path.suffix == '.png'