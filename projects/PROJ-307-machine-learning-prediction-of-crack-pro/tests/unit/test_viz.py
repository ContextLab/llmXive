"""
Unit tests for visualization logic in code/analysis/viz.py.
"""
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

# Import the functions to test
from analysis.viz import generate_pd_plot, plot_log_log_scatter


class TestGeneratePdPlot:
    """Tests for generate_pd_plot function."""

    def test_generate_pd_plot_creates_file(self, tmp_path):
        """Test that PDP generation creates the output file."""
        # Create dummy data
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame({
            'log_delta_k': np.random.uniform(2, 5, n_samples),
            'other_feature': np.random.uniform(0, 1, n_samples)
        })
        
        # Train a simple linear model (mocking the baseline model)
        y = 2.0 * X['log_delta_k'] + np.random.normal(0, 0.1, n_samples)
        model = LinearRegression().fit(X, y)
        
        output_file = tmp_path / "test_pdp.png"
        
        # Run the function
        result_path = generate_pd_plot(
            model=model,
            X=X,
            feature_name='log_delta_k',
            output_path=str(output_file)
        )
        
        # Assertions
        assert result_path == output_file
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_generate_pd_plot_invalid_feature(self):
        """Test that invalid feature name raises error."""
        X = pd.DataFrame({'log_delta_k': [1, 2, 3]})
        model = LinearRegression().fit(X, [1, 2, 3])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "fail.png"
            with pytest.raises((KeyError, ValueError)):
                generate_pd_plot(
                    model=model,
                    X=X,
                    feature_name='non_existent_feature',
                    output_path=str(output_path)
                )


class TestPlotLogLogScatter:
    """Tests for plot_log_log_scatter function."""

    def test_plot_log_log_scatter_creates_file(self, tmp_path):
        """Test that log-log scatter plot creates the output file."""
        # Create dummy data with positive values
        np.random.seed(42)
        data = {
            'delta_k': np.logspace(2, 4, 50),
            'da_dn': np.logspace(-6, -4, 50)
        }
        df = pd.DataFrame(data)
        
        output_file = tmp_path / "test_scatter.png"
        
        # Run the function
        result_path = plot_log_log_scatter(
            df=df,
            x_col='delta_k',
            y_col='da_dn',
            output_path=str(output_file)
        )
        
        # Assertions
        assert result_path == output_file
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_plot_log_log_scatter_non_positive_values(self, tmp_path):
        """Test handling of non-positive values (should filter or warn)."""
        # Create data with a zero/negative value
        data = {
            'delta_k': [1.0, 2.0, 0.0, 4.0],
            'da_dn': [1e-6, 2e-6, 1e-5, 4e-6]
        }
        df = pd.DataFrame(data)
        
        output_file = tmp_path / "test_scatter_filter.png"
        
        # Should not raise, but should handle the invalid point
        result_path = plot_log_log_scatter(
            df=df,
            x_col='delta_k',
            y_col='da_dn',
            output_path=str(output_file)
        )
        
        assert output_file.exists()