"""
Unit tests for visualization generation (T037 - US3).

Tests verify:
- Scatter plot creation with regression lines
- Clone density vs perplexity plots
- Clone density vs accuracy plots
- Sensitivity analysis plots
- Output file generation (PNG & PDF)
- Error handling for invalid data
"""
import pytest
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, PropertyMock

# Import visualization module functions
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
from config import get_figure_format, get_figure_dpi, get_clone_thresholds
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_returns_logger(self):
        """Verify setup_logging returns a valid logger instance."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == 'visualization'
        
    def test_setup_logging_creates_file_handler(self):
        """Verify logging creates appropriate handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / 'test.log'
            logger = setup_logging()
            assert len(logger.handlers) > 0
            

class TestLoadCorrelationData:
    """Tests for load_correlation_data function."""
    
    def test_load_correlation_data_with_valid_csv(self):
        """Verify data loading from valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_correlation.csv'
            
            # Create test data
            data = {
                'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
                'perplexity': [10.5, 11.2, 12.1, 13.0, 14.2],
                'accuracy': [0.85, 0.82, 0.78, 0.75, 0.70]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            result = load_correlation_data(csv_path)
            assert result is not None
            assert len(result) == 5
            assert 'clone_density' in result.columns
            assert 'perplexity' in result.columns
            assert 'accuracy' in result.columns
            
    def test_load_correlation_data_with_missing_file(self):
        """Verify error handling for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'nonexistent.csv'
            
            with pytest.raises(FileNotFoundError):
                load_correlation_data(csv_path)
                
    def test_load_correlation_data_with_empty_file(self):
        """Verify handling of empty CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'empty.csv'
            csv_path.touch()
            
            with pytest.raises((pd.errors.EmptyDataError, ValueError)):
                load_correlation_data(csv_path)
                
    def test_load_correlation_data_preserves_columns(self):
        """Verify all expected columns are loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test.csv'
            
            data = {
                'clone_density': [0.1],
                'perplexity': [10.0],
                'accuracy': [0.8],
                'threshold_07': [0.05],
                'threshold_08': [0.03],
                'threshold_09': [0.02]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            result = load_correlation_data(csv_path)
            assert 'threshold_07' in result.columns
            assert 'threshold_08' in result.columns
            assert 'threshold_09' in result.columns
            

class TestComputeRegression:
    """Tests for compute_regression function."""
    
    def test_compute_regression_basic(self):
        """Verify basic linear regression computation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])  # Perfect linear relationship
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert isinstance(slope, (int, float, np.number))
        assert isinstance(intercept, (int, float, np.number))
        assert isinstance(r_squared, (int, float, np.number))
        assert np.isclose(slope, 2.0, atol=0.1)
        assert np.isclose(intercept, 0.0, atol=0.1)
        assert np.isclose(r_squared, 1.0, atol=0.01)
        
    def test_compute_regression_with_noise(self):
        """Verify regression with noisy data."""
        np.random.seed(42)
        x = np.linspace(0, 10, 50)
        y = 2 * x + 1 + np.random.normal(0, 2, 50)
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert isinstance(slope, (int, float, np.number))
        assert isinstance(intercept, (int, float, np.number))
        assert isinstance(r_squared, (int, float, np.number))
        assert 0 <= r_squared <= 1  # R-squared should be in valid range
        
    def test_compute_regression_constant_y(self):
        """Verify handling of constant y values."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])  # Constant values
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert np.isclose(slope, 0.0, atol=0.001)
        assert np.isclose(intercept, 5.0, atol=0.001)
        assert np.isclose(r_squared, 0.0, atol=0.001)
        
    def test_compute_regression_single_point(self):
        """Verify error handling for single data point."""
        x = np.array([1])
        y = np.array([2])
        
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            compute_regression(x, y)
            
    def test_compute_regression_with_nan(self):
        """Verify handling of NaN values."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        # Should either handle NaN or raise appropriate error
        assert isinstance(slope, (int, float, np.number))
        assert isinstance(intercept, (int, float, np.number))
        
    def test_compute_regression_with_inf(self):
        """Verify handling of infinite values."""
        x = np.array([1, 2, np.inf, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        # Should handle or raise appropriate error
        with pytest.raises((ValueError, np.linalg.LinAlgError)):
            compute_regression(x, y)
            
    def test_compute_regression_svd_convergence(self):
        """Verify handling of SVD convergence issues (robustness)."""
        # Create ill-conditioned data that might cause SVD issues
        x = np.array([1, 1.0000001, 1.0000002, 1.0000003, 1.0000004])
        y = np.array([2, 2, 2, 2, 2])
        
        # Should handle gracefully or raise informative error
        try:
            slope, intercept, r_squared = compute_regression(x, y)
            assert isinstance(slope, (int, float, np.number))
        except np.linalg.LinAlgError:
            # Acceptable - function may raise for ill-conditioned data
            pass
            

class TestCreateScatterPlotWithRegression:
    """Tests for create_scatter_plot_with_regression function."""
    
    def test_create_scatter_plot_creates_figure(self):
        """Verify scatter plot creates valid matplotlib figure."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        fig, ax = create_scatter_plot_with_regression(x, y, 'Test X', 'Test Y')
        
        assert fig is not None
        assert ax is not None
        assert len(ax.collections) > 0  # Scatter points exist
        assert len(ax.lines) > 0  # Regression line exists
        
        plt.close(fig)
        
    def test_create_scatter_plot_with_labels(self):
        """Verify axis labels are set correctly."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        fig, ax = create_scatter_plot_with_regression(x, y, 'Clone Density', 'Perplexity')
        
        assert ax.get_xlabel() == 'Clone Density'
        assert ax.get_ylabel() == 'Perplexity'
        
        plt.close(fig)
        
    def test_create_scatter_plot_with_title(self):
        """Verify plot title is set correctly."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        fig, ax = create_scatter_plot_with_regression(x, y, 'X', 'Y', title='Test Title')
        
        assert ax.get_title() == 'Test Title'
        
        plt.close(fig)
        
    def test_create_scatter_plot_with_r_squared(self):
        """Verify R-squared value is displayed."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        fig, ax = create_scatter_plot_with_regression(x, y, 'X', 'Y', show_r_squared=True)
        
        # Check that text annotation exists
        texts = [child for child in ax.get_children() if hasattr(child, 'get_text')]
        assert len(texts) > 0
        
        plt.close(fig)
        
    def test_create_scatter_plot_empty_data(self):
        """Verify error handling for empty data."""
        x = np.array([])
        y = np.array([])
        
        with pytest.raises((ValueError, IndexError)):
            create_scatter_plot_with_regression(x, y, 'X', 'Y')
            
    def test_create_scatter_plot_mismatched_lengths(self):
        """Verify error handling for mismatched array lengths."""
        x = np.array([1, 2, 3])
        y = np.array([1, 2])
        
        with pytest.raises((ValueError, IndexError)):
            create_scatter_plot_with_regression(x, y, 'X', 'Y')
            
    def test_create_scatter_plot_save_to_file(self):
        """Verify plot can be saved to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            x = np.array([1, 2, 3, 4, 5])
            y = np.array([2, 4, 6, 8, 10])
            
            output_path = Path(tmpdir) / 'test_scatter.png'
            fig, ax = create_scatter_plot_with_regression(x, y, 'X', 'Y')
            fig.savefig(output_path)
            
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            plt.close(fig)
            

class TestCreateCloneDensityVsPerplexityPlot:
    """Tests for create_clone_density_vs_perplexity_plot function."""
    
    def test_create_clone_density_vs_perplexity_plot(self):
        """Verify clone density vs perplexity plot creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_metrics.csv'
            
            data = {
                'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
                'perplexity': [10.5, 11.2, 12.1, 13.0, 14.2]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / 'clone_vs_perplexity.png'
            fig = create_clone_density_vs_perplexity_plot(csv_path, output_path)
            
            assert fig is not None
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            plt.close(fig)
            
    def test_create_clone_density_vs_perplexity_plot_pdf(self):
        """Verify PDF output format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_metrics.csv'
            data = {
                'clone_density': [0.1, 0.2, 0.3],
                'perplexity': [10.0, 11.0, 12.0]
            }
            pd.DataFrame(data).to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / 'clone_vs_perplexity.pdf'
            fig = create_clone_density_vs_perplexity_plot(csv_path, output_path)
            
            assert output_path.exists()
            assert output_path.suffix == '.pdf'
            
            plt.close(fig)
            
    def test_create_clone_density_vs_perplexity_plot_missing_data(self):
        """Verify handling of missing data columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'incomplete.csv'
            data = {'clone_density': [0.1, 0.2]}  # Missing perplexity
            pd.DataFrame(data).to_csv(csv_path, index=False)
            
            with pytest.raises((KeyError, ValueError)):
                create_clone_density_vs_perplexity_plot(csv_path, Path(tmpdir) / 'out.png')
                

class TestCreateCloneDensityVsAccuracyPlot:
    """Tests for create_clone_density_vs_accuracy_plot function."""
    
    def test_create_clone_density_vs_accuracy_plot(self):
        """Verify clone density vs accuracy plot creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_metrics.csv'
            
            data = {
                'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
                'accuracy': [0.85, 0.82, 0.78, 0.75, 0.70]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / 'clone_vs_accuracy.png'
            fig = create_clone_density_vs_accuracy_plot(csv_path, output_path)
            
            assert fig is not None
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            plt.close(fig)
            
    def test_create_clone_density_vs_accuracy_plot_negative_correlation(self):
        """Verify plot handles negative correlation correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'test_metrics.csv'
            
            # Perfect negative correlation
            data = {
                'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
                'accuracy': [0.95, 0.85, 0.75, 0.65, 0.55]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / 'clone_vs_accuracy.png'
            fig = create_clone_density_vs_accuracy_plot(csv_path, output_path)
            
            assert fig is not None
            assert output_path.exists()
            
            plt.close(fig)
            

class TestCreateSensitivityAnalysisPlot:
    """Tests for create_sensitivity_analysis_plot function."""
    
    def test_create_sensitivity_analysis_plot(self):
        """Verify sensitivity analysis plot creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'sensitivity.csv'
            
            # Create sensitivity analysis data for multiple thresholds
            data = {
                'threshold': [0.7, 0.8, 0.9],
                'correlation_perplexity': [0.45, 0.52, 0.48],
                'correlation_accuracy': [-0.38, -0.42, -0.40],
                'p_value_perplexity': [0.001, 0.0005, 0.0012],
                'p_value_accuracy': [0.002, 0.001, 0.0018]
            }
            df = pd.DataFrame(data)
            df.to_csv(csv_path, index=False)
            
            output_path = Path(tmpdir) / 'sensitivity_analysis.png'
            fig = create_sensitivity_analysis_plot(csv_path, output_path)
            
            assert fig is not None
            assert output_path.exists()
            assert output_path.stat().st_size > 0
            
            plt.close(fig)
            
    def test_create_sensitivity_analysis_plot_with_thresholds(self):
        """Verify plot uses configured thresholds."""
        thresholds = get_clone_thresholds()
        assert len(thresholds) >= 3
        assert 0.7 in thresholds
        assert 0.8 in thresholds
        assert 0.9 in thresholds
        
    def test_create_sensitivity_analysis_plot_missing_columns(self):
        """Verify error handling for missing sensitivity columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'incomplete.csv'
            data = {'threshold': [0.7, 0.8]}  # Missing correlation columns
            pd.DataFrame(data).to_csv(csv_path, index=False)
            
            with pytest.raises((KeyError, ValueError)):
                create_sensitivity_analysis_plot(csv_path, Path(tmpdir) / 'out.png')
                

class TestGenerateAllVisualizations:
    """Tests for generate_all_visualizations function."""
    
    def test_generate_all_visualizations_creates_all_plots(self):
        """Verify all visualization types are generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data files
            metrics_path = Path(tmpdir) / 'clone_metrics.csv'
            data = {
                'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
                'perplexity': [10.5, 11.2, 12.1, 13.0, 14.2],
                'accuracy': [0.85, 0.82, 0.78, 0.75, 0.70]
            }
            pd.DataFrame(data).to_csv(metrics_path, index=False)
            
            correlation_path = Path(tmpdir) / 'correlation_results.csv'
            corr_data = {
                'threshold': [0.7, 0.8, 0.9],
                'correlation_perplexity': [0.45, 0.52, 0.48],
                'correlation_accuracy': [-0.38, -0.42, -0.40],
                'p_value_perplexity': [0.001, 0.0005, 0.0012],
                'p_value_accuracy': [0.002, 0.001, 0.0018]
            }
            pd.DataFrame(corr_data).to_csv(correlation_path, index=False)
            
            output_dir = Path(tmpdir) / 'figures'
            output_dir.mkdir()
            
            results = generate_all_visualizations(
                metrics_path,
                correlation_path,
                output_dir
            )
            
            assert results is not None
            assert 'scatter_perplexity' in results or len(results) > 0
            
            # Verify output files exist
            output_files = list(output_dir.glob('*.png'))
            assert len(output_files) > 0
            
    def test_generate_all_visualizations_with_pdf_output(self):
        """Verify PDF output format is supported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / 'clone_metrics.csv'
            data = {
                'clone_density': [0.1, 0.2, 0.3],
                'perplexity': [10.0, 11.0, 12.0],
                'accuracy': [0.8, 0.75, 0.7]
            }
            pd.DataFrame(data).to_csv(metrics_path, index=False)
            
            correlation_path = Path(tmpdir) / 'correlation_results.csv'
            corr_data = {
                'threshold': [0.7, 0.8, 0.9],
                'correlation_perplexity': [0.45, 0.52, 0.48],
                'correlation_accuracy': [-0.38, -0.42, -0.40],
                'p_value_perplexity': [0.001, 0.0005, 0.0012],
                'p_value_accuracy': [0.002, 0.001, 0.0018]
            }
            pd.DataFrame(corr_data).to_csv(correlation_path, index=False)
            
            output_dir = Path(tmpdir) / 'figures'
            output_dir.mkdir()
            
            results = generate_all_visualizations(
                metrics_path,
                correlation_path,
                output_dir,
                figure_format='pdf'
            )
            
            pdf_files = list(output_dir.glob('*.pdf'))
            assert len(pdf_files) > 0
            
    def test_generate_all_visualizations_missing_input(self):
        """Verify error handling for missing input files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'figures'
            output_dir.mkdir()
            
            with pytest.raises(FileNotFoundError):
                generate_all_visualizations(
                    Path(tmpdir) / 'nonexistent.csv',
                    Path(tmpdir) / 'nonexistent2.csv',
                    output_dir
                )
                
    def test_generate_all_visualizations_output_directory_creation(self):
        """Verify output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / 'clone_metrics.csv'
            data = {
                'clone_density': [0.1, 0.2, 0.3],
                'perplexity': [10.0, 11.0, 12.0],
                'accuracy': [0.8, 0.75, 0.7]
            }
            pd.DataFrame(data).to_csv(metrics_path, index=False)
            
            correlation_path = Path(tmpdir) / 'correlation_results.csv'
            corr_data = {
                'threshold': [0.7, 0.8, 0.9],
                'correlation_perplexity': [0.45, 0.52, 0.48],
                'correlation_accuracy': [-0.38, -0.42, -0.40],
                'p_value_perplexity': [0.001, 0.0005, 0.0012],
                'p_value_accuracy': [0.002, 0.001, 0.0018]
            }
            pd.DataFrame(corr_data).to_csv(correlation_path, index=False)
            
            output_dir = Path(tmpdir) / 'new_figures'
            assert not output_dir.exists()
            
            results = generate_all_visualizations(
                metrics_path,
                correlation_path,
                output_dir
            )
            
            assert output_dir.exists()
            

class TestVisualizationConfig:
    """Tests for visualization configuration."""
    
    def test_get_figure_format(self):
        """Verify figure format configuration."""
        fmt = get_figure_format()
        assert fmt in ['png', 'pdf', 'both']
        
    def test_get_figure_dpi(self):
        """Verify figure DPI configuration."""
        dpi = get_figure_dpi()
        assert isinstance(dpi, (int, float))
        assert dpi >= 72  # Minimum reasonable DPI
        
    def test_get_clone_thresholds(self):
        """Verify clone thresholds configuration includes 0.7, 0.8, 0.9."""
        thresholds = get_clone_thresholds()
        assert 0.7 in thresholds, "Threshold 0.7 must be in clone_thresholds"
        assert 0.8 in thresholds, "Threshold 0.8 must be in clone_thresholds"
        assert 0.9 in thresholds, "Threshold 0.9 must be in clone_thresholds"
        

class TestVisualizationEdgeCases:
    """Edge case tests for visualization functions."""
    
    def test_visualization_with_single_data_point(self):
        """Verify handling of single data point."""
        x = np.array([1])
        y = np.array([2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'single_point.png'
            fig = create_scatter_plot_with_regression(x, y, 'X', 'Y')
            fig.savefig(output_path)
            
            assert output_path.exists()
            plt.close(fig)
            
    def test_visualization_with_zero_variance(self):
        """Verify handling of zero variance data."""
        x = np.array([1, 1, 1, 1, 1])
        y = np.array([2, 2, 2, 2, 2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'zero_var.png'
            fig = create_scatter_plot_with_regression(x, y, 'X', 'Y')
            fig.savefig(output_path)
            
            assert output_path.exists()
            plt.close(fig)
            
    def test_visualization_with_large_dataset(self):
        """Verify handling of large datasets."""
        np.random.seed(42)
        x = np.random.randn(10000)
        y = 2 * x + np.random.randn(10000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'large_dataset.png'
            fig = create_scatter_plot_with_regression(x, y, 'X', 'Y')
            fig.savefig(output_path)
            
            assert output_path.exists()
            plt.close(fig)
            
    def test_visualization_memory_cleanup(self):
        """Verify figures are properly closed after use."""
        import gc
        
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        for _ in range(10):
            fig, ax = create_scatter_plot_with_regression(x, y, 'X', 'Y')
            plt.close(fig)
            
        gc.collect()
        
        # Verify no memory leak (matplotlib should clean up)
        assert len(plt.get_fignums()) == 0
            

class TestVisualizationRegressionRobustness:
    """Tests for regression computation robustness (addresses SVD convergence issues)."""
    
    def test_regression_with_ill_conditioned_data(self):
        """Verify regression handles ill-conditioned matrices."""
        # Create nearly collinear data
        x = np.array([1, 1.000001, 1.000002, 1.000003, 1.000004])
        y = np.array([2, 2.000001, 2.000002, 2.000003, 2.000004])
        
        try:
            slope, intercept, r_squared = compute_regression(x, y)
            assert isinstance(slope, (int, float, np.number))
        except np.linalg.LinAlgError:
            # Acceptable - function may raise for ill-conditioned data
            pass
            
    def test_regression_with_extreme_values(self):
        """Verify regression handles extreme values."""
        x = np.array([1e-10, 1e-9, 1e-8, 1e-7, 1e-6])
        y = np.array([1e10, 1e11, 1e12, 1e13, 1e14])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert isinstance(slope, (int, float, np.number))
        assert isinstance(intercept, (int, float, np.number))
        assert isinstance(r_squared, (int, float, np.number))
        
    def test_regression_with_mixed_sign_data(self):
        """Verify regression handles data with mixed signs."""
        x = np.array([-5, -3, -1, 1, 3, 5])
        y = np.array([-10, -6, -2, 2, 6, 10])
        
        slope, intercept, r_squared = compute_regression(x, y)
        
        assert np.isclose(slope, 2.0, atol=0.1)
        assert np.isclose(intercept, 0.0, atol=0.1)
        assert np.isclose(r_squared, 1.0, atol=0.01)
            

if __name__ == '__main__':
    pytest.main([__file__, '-v'])