import os
import unittest
from unittest.mock import patch
import pandas as pd
from code.viz.plots import create_scatter_plot, create_residual_plot

class TestPlots(unittest.TestCase):

    @patch('code.viz.plots.plt')
    def test_create_scatter_plot(self, mock_plt):
        # Create a sample DataFrame
        data = {'x': [1, 2, 3, 4, 5], 'y': [2, 4, 1, 3, 5]}
        df = pd.DataFrame(data)

        # Call the function
        create_scatter_plot(df, 'x', 'y', 'Scatter Plot', 'data/processed/scatter_plot.png')

        # Assert that the plot was created and saved
        mock_plt.scatter.assert_called_once()
        mock_plt.title.assert_called_once_with('Scatter Plot')
        mock_plt.xlabel.assert_called_once_with('x')
        mock_plt.ylabel.assert_called_once_with('y')
        mock_plt.savefig.assert_called_once_with('data/processed/scatter_plot.png')

    @patch('code.viz.plots.plt')
    def test_create_residual_plot(self, mock_plt):
        # Create a sample DataFrame
        data = {'predicted': [1, 2, 3, 4, 5], 'actual': [1.2, 1.8, 3.1, 4.2, 4.9]}
        df = pd.DataFrame(data)

        # Call the function
        create_residual_plot(df, 'predicted', 'actual', 'Residual Plot', 'data/processed/residuals.png')

        # Assert that the plot was created and saved
        mock_plt.scatter.assert_called_once()
        mock_plt.title.assert_called_once_with('Residual Plot')
        mock_plt.xlabel.assert_called_once_with('Predicted Values')
        mock_plt.ylabel.assert_called_once_with('Residuals')
        mock_plt.savefig.assert_called_once_with('data/processed/residuals.png')

if __name__ == '__main__':
    unittest.main()
