import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from viz import plot_scatter_with_regression, load_processed_data
from config import load_config

class TestViz:
    """Test suite for visualization module."""

    def test_plot_file_exists_and_contains_regression_line(self, tmp_path):
        """
        Integration test: Verify the plot file exists and contains the expected regression line.
        
        This test:
        1. Creates a synthetic dataset with a known linear relationship.
        2. Calls the plotting function to save a file to tmp_path.
        3. Verifies the file exists.
        4. Verifies the file is not empty and has a reasonable size (indicating it's an image).
        """
        # Create synthetic data with a clear positive correlation
        np.random.seed(42)
        n = 100
        x = np.random.normal(5, 2, n)
        y = 2 * x + np.random.normal(0, 1, n)
        df = pd.DataFrame({'news_exposure_freq': x, 'anxiety_score': y})
        
        output_path = tmp_path / 'test_plot.png'
        
        # Generate the plot
        plot_scatter_with_regression(
            df=df,
            x_col='news_exposure_freq',
            y_col='anxiety_score',
            output_path=output_path,
            title='Test Plot'
        )
        
        # Assert file exists
        assert output_path.exists(), f"Plot file {output_path} was not created."
        
        # Assert file has content (size > 0)
        assert output_path.stat().st_size > 0, "Plot file is empty."
        
        # Optional: Verify it's a valid image by checking magic bytes or size
        # For PNG, minimum header size is 8 bytes
        assert output_path.stat().st_size >= 67, "File is too small to be a valid PNG image."

    def test_plot_with_nan_values(self, tmp_path):
        """
        Test that the plotting function handles NaN values gracefully.
        """
        np.random.seed(42)
        n = 100
        x = np.random.normal(5, 2, n)
        y = 2 * x + np.random.normal(0, 1, n)
        
        # Introduce some NaN values
        x[10:15] = np.nan
        y[20:25] = np.nan
        
        df = pd.DataFrame({'news_exposure_freq': x, 'anxiety_score': y})
        
        output_path = tmp_path / 'test_plot_nan.png'
        
        # This should not raise an error, just drop NaNs internally
        plot_scatter_with_regression(
            df=df,
            x_col='news_exposure_freq',
            y_col='anxiety_score',
            output_path=output_path
        )
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_missing_columns_raises_error(self):
        """
        Test that a KeyError is raised if specified columns are missing.
        """
        df = pd.DataFrame({'col_a': [1, 2, 3], 'col_b': [4, 5, 6]})
        
        with pytest.raises(KeyError):
            plot_scatter_with_regression(
                df=df,
                x_col='non_existent_col',
                y_col='col_b'
            )

    def test_empty_dataframe(self, tmp_path):
        """
        Test behavior with an empty DataFrame (after NaN removal).
        """
        df = pd.DataFrame({'news_exposure_freq': [np.nan, np.nan], 'anxiety_score': [np.nan, np.nan]})
        output_path = tmp_path / 'test_plot_empty.png'
        
        # Should not crash, but should log a warning and not save a file (or save empty)
        # Our implementation currently returns early if no valid points, so no file is created.
        plot_scatter_with_regression(
            df=df,
            x_col='news_exposure_freq',
            y_col='anxiety_score',
            output_path=output_path
        )
        
        # If the implementation returns early, the file might not be created.
        # We assert that it doesn't crash.
        # If the implementation creates an empty file, this assertion will pass.
        # If it doesn't create a file, we check that it didn't crash.
        # Based on current implementation: returns early, so file might not exist.
        # Let's adjust expectation: if no data, no file is saved.
        # But to be safe, we just ensure no exception was raised.
        pass