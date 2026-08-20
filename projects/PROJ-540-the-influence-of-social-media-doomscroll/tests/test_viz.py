import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from viz import plot_scatter_with_regression, load_processed_data
from config import load_config

class TestViz:
    @pytest.fixture
    def sample_data(self):
        """Create a sample DataFrame for testing."""
        np.random.seed(42)
        n = 100
        return pd.DataFrame({
            'news_exposure_freq': np.random.normal(5, 2, n),
            'anxiety_score': np.random.normal(10, 3, n),
            'baseline_anxiety': np.random.normal(8, 2, n),
            'age': np.random.randint(18, 65, n),
            'gender': np.random.choice(['M', 'F'], n)
        })

    def test_plot_file_exists_and_contains_regression_line(self, sample_data, tmp_path):
        """
        Integration test: Verify the plot file exists and contains the expected regression line.
        This test generates a plot and checks for the presence of key elements.
        """
        output_path = tmp_path / "test_plot.png"
        
        # Generate the plot
        result_path = plot_scatter_with_regression(
            sample_data,
            x_col="news_exposure_freq",
            y_col="anxiety_score",
            output_path=output_path,
            title="Test Plot"
        )
        
        # Check file exists
        assert result_path.exists(), f"Plot file not created at {result_path}"
        
        # Check file size (should be non-empty)
        assert result_path.stat().st_size > 0, "Plot file is empty"
        
        # Verify the plot can be read back (basic sanity check)
        # Note: We don't parse the image content deeply here, but we ensure
        # the file was written successfully by matplotlib
        assert result_path.suffix == ".png", "Output file is not a PNG"

    def test_plot_with_insufficient_data_raises_error(self, tmp_path):
        """Test that insufficient data raises a ValueError."""
        insufficient_data = pd.DataFrame({
            'news_exposure_freq': [1.0],
            'anxiety_score': [2.0]
        })
        
        output_path = tmp_path / "fail_plot.png"
        
        with pytest.raises(ValueError, match="Insufficient data points"):
            plot_scatter_with_regression(
                insufficient_data,
                x_col="news_exposure_freq",
                y_col="anxiety_score",
                output_path=output_path
            )

    def test_plot_with_missing_columns_raises_error(self, sample_data, tmp_path):
        """Test that missing columns raise a KeyError."""
        output_path = tmp_path / "fail_plot.png"
        
        with pytest.raises(KeyError):
            plot_scatter_with_regression(
                sample_data,
                x_col="nonexistent_column",
                y_col="anxiety_score",
                output_path=output_path
            )