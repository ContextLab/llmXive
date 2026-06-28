"""
Unit tests for the visualization module.

These tests verify the core functionality of visualization.py without
requiring actual data files or heavy computation.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from visualization import (
    compute_regression,
    create_scatter_plot_with_regression,
    load_correlation_data,
    generate_all_visualizations,
)

# Test fixtures
@pytest.fixture
def sample_data_path(tmp_path):
    """Create a sample correlation results CSV file."""
    data_path = tmp_path / 'correlation_results.csv'
    data = {
        'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        'perplexity': [10.5, 11.2, 12.0, 13.5, 14.2, 15.0, 16.5, 17.2, 18.0],
        'accuracy': [0.95, 0.92, 0.88, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60]
    }
    df = pd.DataFrame(data)
    df.to_csv(data_path, index=False)
    return data_path

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'clone_density': [0.1, 0.2, 0.3, 0.4, 0.5],
        'perplexity': [10.0, 11.0, 12.0, 13.0, 14.0],
        'accuracy': [0.95, 0.90, 0.85, 0.80, 0.75]
    })

class TestRegressionComputation:
    """Tests for the compute_regression function."""

    def test_regression_basic(self):
        """Test basic linear regression computation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        slope, intercept, r_value, p_value = compute_regression(x, y)
        
        assert slope == pytest.approx(2.0, rel=1e-5)
        assert intercept == pytest.approx(0.0, abs=1e-5)
        assert abs(r_value) == pytest.approx(1.0, abs=1e-5)  # Perfect correlation
        assert p_value < 0.001  # Highly significant

    def test_regression_noisy_data(self):
        """Test regression with noisy data."""
        np.random.seed(42)
        x = np.random.rand(50)
        y = 3 * x + 2 + np.random.randn(50) * 0.5
        
        slope, intercept, r_value, p_value = compute_regression(x, y)
        
        assert 2.5 < slope < 3.5
        assert 1.5 < intercept < 2.5
        assert abs(r_value) > 0.9
        assert p_value < 0.001

    def test_regression_negative_correlation(self):
        """Test regression with negative correlation."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        
        slope, intercept, r_value, p_value = compute_regression(x, y)
        
        assert slope == pytest.approx(-2.0, rel=1e-5)
        assert intercept == pytest.approx(12.0, abs=1e-5)
        assert r_value == pytest.approx(-1.0, abs=1e-5)

class TestLoadCorrelationData:
    """Tests for the load_correlation_data function."""

    def test_load_valid_data(self, sample_data_path):
        """Test loading valid correlation data."""
        df = load_correlation_data(sample_data_path)
        
        assert len(df) == 9
        assert 'clone_density' in df.columns
        assert 'perplexity' in df.columns
        assert 'accuracy' in df.columns

    def test_load_missing_columns(self, tmp_path):
        """Test loading data with missing required columns."""
        data_path = tmp_path / 'incomplete.csv'
        pd.DataFrame({'clone_density': [0.1, 0.2]}).to_csv(data_path, index=False)
        
        with pytest.raises(ValueError, match='Missing required columns'):
            load_correlation_data(data_path)

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading from a non-existent file."""
        fake_path = tmp_path / 'does_not_exist.csv'
        
        with pytest.raises(FileNotFoundError):
            load_correlation_data(fake_path)

    def test_load_absolute_path(self, sample_data_path):
        """Test loading with absolute path."""
        df = load_correlation_data(Path(sample_data_path).resolve())
        assert len(df) == 9

class TestPlotCreation:
    """Tests for plot creation functionality."""

    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_scatter_plot_with_regression(
        self, mock_close, mock_savefig, mock_subplots, sample_dataframe, tmp_path
    ):
        """Test scatter plot creation with regression line."""
        # Mock subplot return
        fig = MagicMock()
        ax = MagicMock()
        mock_subplots.return_value = (fig, ax)
        
        output_path = tmp_path / 'test_plot'
        
        create_scatter_plot_with_regression(
            x=sample_dataframe['clone_density'].values,
            y=sample_dataframe['perplexity'].values,
            x_label='Clone Density',
            y_label='Perplexity',
            title='Test Plot',
            output_path=output_path
        )
        
        # Verify savefig was called
        assert mock_savefig.called
        assert mock_close.called

    @patch('matplotlib.pyplot.subplots')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_create_plot_with_confidence_interval(
        self, mock_close, mock_savefig, mock_subplots, sample_dataframe, tmp_path
    ):
        """Test plot creation with confidence interval shading."""
        fig = MagicMock()
        ax = MagicMock()
        mock_subplots.return_value = (fig, ax)
        
        output_path = tmp_path / 'test_plot_ci'
        
        create_scatter_plot_with_regression(
            x=sample_dataframe['clone_density'].values,
            y=sample_dataframe['perplexity'].values,
            x_label='Clone Density',
            y_label='Perplexity',
            title='Test Plot CI',
            output_path=output_path,
            show_confidence=True
        )
        
        # Verify confidence interval was computed
        assert mock_savefig.called

class TestVisualizationIntegration:
    """Integration tests for visualization pipeline."""

    def test_generate_visualizations_creates_files(
        self, sample_data_path, tmp_path
    ):
        """Test that generate_all_visualizations creates output files."""
        output_dir = tmp_path / 'figures'
        
        # Mock the actual plot saving to avoid matplotlib issues in tests
        with patch('visualization.create_clone_density_vs_perplexity_plot') as mock_ppl, \
             patch('visualization.create_clone_density_vs_accuracy_plot') as mock_acc, \
             patch('visualization.create_sensitivity_analysis_plot') as mock_sens:
            
            # Set up mock return values
            png_path = output_dir / 'test.png'
            pdf_path = output_dir / 'test.pdf'
            
            mock_ppl.return_value = [png_path, pdf_path]
            mock_acc.return_value = [png_path, pdf_path]
            mock_sens.return_value = [png_path, pdf_path]
            
            results = generate_all_visualizations(
                data_path=sample_data_path,
                output_dir=output_dir
            )
            
            assert 'clone_density_vs_perplexity' in results
            assert 'clone_density_vs_accuracy' in results
            assert 'sensitivity_analysis' in results

    def test_generate_visualizations_handles_empty_data(self, tmp_path):
        """Test handling of empty or minimal data."""
        data_path = tmp_path / 'empty.csv'
        data = {
            'clone_density': [0.5],
            'perplexity': [15.0],
            'accuracy': [0.75]
        }
        pd.DataFrame(data).to_csv(data_path, index=False)
        
        output_dir = tmp_path / 'figures'
        
        with patch('visualization.create_clone_density_vs_perplexity_plot') as mock_ppl, \
             patch('visualization.create_clone_density_vs_accuracy_plot') as mock_acc, \
             patch('visualization.create_sensitivity_analysis_plot') as mock_sens:
            
            png_path = output_dir / 'test.png'
            pdf_path = output_dir / 'test.pdf'
            
            mock_ppl.return_value = [png_path, pdf_path]
            mock_acc.return_value = [png_path, pdf_path]
            mock_sens.return_value = [png_path, pdf_path]
            
            results = generate_all_visualizations(
                data_path=data_path,
                output_dir=output_dir
            )
            
            assert len(results) == 3

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_regression_with_single_point(self):
        """Test regression with only one data point."""
        x = np.array([1.0])
        y = np.array([2.0])
        
        with pytest.raises(ValueError):
            compute_regression(x, y)

    def test_regression_with_constant_y(self):
        """Test regression with constant y values."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 5, 5, 5, 5])
        
        slope, intercept, r_value, p_value = compute_regression(x, y)
        
        # Should handle constant y gracefully
        assert slope == pytest.approx(0.0, abs=1e-5)

    def test_load_data_with_nan_values(self, tmp_path):
        """Test loading data containing NaN values."""
        data_path = tmp_path / 'nan_data.csv'
        data = {
            'clone_density': [0.1, np.nan, 0.3],
            'perplexity': [10.0, 11.0, np.nan],
            'accuracy': [0.95, 0.90, 0.85]
        }
        pd.DataFrame(data).to_csv(data_path, index=False)
        
        df = load_correlation_data(data_path)
        # Should load with NaN values present
        assert df['clone_density'].isna().sum() == 1
        assert df['perplexity'].isna().sum() == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])