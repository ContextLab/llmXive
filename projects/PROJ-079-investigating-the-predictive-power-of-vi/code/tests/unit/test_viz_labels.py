import pytest
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNet
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pickle

# Import the functions to test from the source module
# Note: The project structure uses 'code/src' as the root for src imports
import sys
import os
# Ensure the code directory is in the path so we can import src.viz
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root / 'src') not in sys.path:
    sys.path.insert(0, str(code_root / 'src'))

from viz import plot_coefficients, plot_partial_dependence
from config import ARTIFACTS_PATH


class TestVizLabels:
    """Tests for T040b: Verify plot labels are set correctly."""

    @pytest.fixture
    def mock_model(self):
        """Create a mock ElasticNet model with coefficients."""
        model = ElasticNet(alpha=0.1, max_iter=1000)
        # We won't actually fit it, but we need it to have coef_ for the viz functions
        # to potentially access if they inspect the model.
        # The functions in viz.py likely calculate coefficients based on the model or data.
        # We mock the model to ensure it doesn't crash during import/setup if it tries to fit.
        return model

    @pytest.fixture
    def mock_data(self):
        """Create mock feature data and target."""
        np.random.seed(42)
        n_samples = 50
        n_features = 10
        X = pd.DataFrame(
            np.random.rand(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
        y = pd.Series(np.random.rand(n_samples))
        return X, y

    @pytest.fixture
    def temp_plot_dir(self):
        """Create a temporary directory for plot outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_plot_coefficients_has_labels(self, mock_model, mock_data, temp_plot_dir):
        """Verify plot_coefficients sets xlabel, ylabel, title, and legend."""
        X, y = mock_data

        # Mock the model's coef_ attribute since we didn't fit it
        # The function might access model.coef_ or model.intercept_
        # We simulate a fitted state
        mock_model.coef_ = np.random.rand(len(X.columns))
        mock_model.intercept_ = 0.0

        # Patch matplotlib to capture the axes object without saving to disk
        # or to verify the state of the figure before saving
        fig, ax = plt.subplots()
        # We need to ensure the function uses this specific axes or creates a new one
        # and sets labels on it. The function signature is plot_coefficients(model, features)
        # It likely creates its own figure. We will patch the plt.gca() or plt.figure to intercept.

        # Strategy: Patch the plt.savefig or plt.show to verify labels after the function runs
        # But simpler: Run the function, then check the current axes (if it uses gca)
        # or rely on the fact that it creates a figure and we can inspect it.
        # Looking at typical implementations, they often use plt.subplots() internally.
        # We will patch the internal call or just run it and check the last active figure/axes.

        # Let's assume the function creates a figure and axes.
        # We can check the state of the axes after the call.
        # To be safe, we'll patch the save path to our temp dir.
        
        # Since the function might create its own figure, we check the current figure/axes
        # after the call. If it creates a new one, it becomes the current one.
        
        # We need to mock the file path to avoid writing to the real ARTIFACTS_PATH
        # The function likely uses a hardcoded path or config. Let's assume it uses config.
        # We can't easily change the config in a unit test without mocking, so we mock the file write.
        
        # Actually, the function signature is `plot_coefficients(model, features)`.
        # It likely determines the output path internally.
        # We will run it and then check the current axes.
        
        # Mock the file system write to prevent actual file creation if needed,
        # but the main goal is to check labels.
        
        # Let's just run it and check the current axes.
        # We need to provide 'features' which are the column names.
        features = X.columns.tolist()
        
        # Mock the model to have coef_
        mock_model.coef_ = np.random.rand(len(features))
        
        # Run the function
        # The function might try to load data or model from disk.
        # We are testing the labeling logic, so we assume the model and features are passed correctly.
        # The function in viz.py: `plot_coefficients(model: Model, features: list)`
        
        # We need to ensure the function doesn't crash.
        # If it tries to load data from disk, we might need to mock that too.
        # But the task is about labels. Let's assume the function is robust enough
        # to work with the passed model and features.
        
        # To avoid file I/O issues, we can patch the Path.write_text or similar if used.
        # But let's try to run it and see. If it fails due to file I/O, we mock that.
        
        # We'll patch the savefig to a dummy function to avoid disk writes if needed,
        # but we want to check the axes BEFORE savefig.
        
        # Better approach: Patch the figure creation to return a known figure/axes
        # and then verify the axes labels.
        
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            # Call the function
            plot_coefficients(mock_model, features)
            
            # Verify that set_xlabel, set_ylabel, set_title, and legend were called
            mock_ax.set_xlabel.assert_called()
            mock_ax.set_ylabel.assert_called()
            mock_ax.set_title.assert_called()
            mock_ax.legend.assert_called()

    def test_plot_partial_dependence_has_labels(self, mock_model, mock_data, temp_plot_dir):
        """Verify plot_partial_dependence sets xlabel, ylabel, title, and legend."""
        X, y = mock_data
        features = X.columns.tolist()
        
        # Mock the model to have coef_
        mock_model.coef_ = np.random.rand(len(features))
        
        # Patch matplotlib to capture axes
        with patch('matplotlib.pyplot.subplots') as mock_subplots:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            mock_subplots.return_value = (mock_fig, mock_ax)
            
            # Call the function
            # plot_partial_dependence(model, X, features, n_points=50)
            plot_partial_dependence(mock_model, X, features, n_points=10) # Use n_points=10 for speed in test
            
            # Verify that set_xlabel, set_ylabel, set_title, and legend were called
            mock_ax.set_xlabel.assert_called()
            mock_ax.set_ylabel.assert_called()
            mock_ax.set_title.assert_called()
            mock_ax.legend.assert_called()