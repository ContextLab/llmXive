import os
import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
from code.viz.plots import create_scatter_plot, create_residual_plot

class TestPlots(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory for test outputs."""
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "data" / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_create_scatter_plot_saves_file(self):
        """Verify that create_scatter_plot generates and saves a PNG file to disk."""
        # Create a sample DataFrame
        data = {
            'x': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'y': [2.1, 3.9, 6.2, 8.1, 10.3, 12.0, 14.1, 16.2, 18.0, 20.1]
        }
        df = pd.DataFrame(data)

        # Define output path
        output_path = str(self.output_dir / "test_scatter.png")

        # Call the function
        create_scatter_plot(df, 'x', 'y', 'Test Scatter Plot', output_path)

        # Assert that the file was created on disk
        self.assertTrue(os.path.exists(output_path), f"Scatter plot file not created at {output_path}")
        self.assertGreater(os.path.getsize(output_path), 0, "Scatter plot file is empty")

    def test_create_residual_plot_saves_file(self):
        """Verify that create_residual_plot generates and saves a PNG file to disk."""
        # Create a sample DataFrame with predicted and actual values
        data = {
            'predicted': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            'actual': [1.2, 1.8, 3.1, 4.2, 4.9, 6.3, 6.8, 8.2, 9.1, 10.2]
        }
        df = pd.DataFrame(data)

        # Define output path
        output_path = str(self.output_dir / "test_residuals.png")

        # Call the function
        create_residual_plot(df, 'predicted', 'actual', 'Test Residual Plot', output_path)

        # Assert that the file was created on disk
        self.assertTrue(os.path.exists(output_path), f"Residual plot file not created at {output_path}")
        self.assertGreater(os.path.getsize(output_path), 0, "Residual plot file is empty")

    def test_create_scatter_plot_with_missing_columns_raises_error(self):
        """Verify that create_scatter_plot raises KeyError if columns are missing."""
        data = {'x': [1, 2, 3], 'y': [4, 5, 6]}
        df = pd.DataFrame(data)
        output_path = str(self.output_dir / "test_error.png")

        with self.assertRaises(KeyError):
            create_scatter_plot(df, 'x', 'non_existent_column', 'Test', output_path)

    def test_create_residual_plot_with_missing_columns_raises_error(self):
        """Verify that create_residual_plot raises KeyError if columns are missing."""
        data = {'predicted': [1, 2, 3], 'actual': [4, 5, 6]}
        df = pd.DataFrame(data)
        output_path = str(self.output_dir / "test_error.png")

        with self.assertRaises(KeyError):
            create_residual_plot(df, 'predicted', 'non_existent_column', 'Test', output_path)

if __name__ == '__main__':
    unittest.main()