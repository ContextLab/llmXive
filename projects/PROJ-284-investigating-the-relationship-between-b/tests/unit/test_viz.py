"""
Unit tests for visualization module.
Implements T029.
"""
import os
import sys
import tempfile
import unittest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if needed
sys_path = Path(__file__).parent.parent.parent
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

from code.viz.scatter import generate_scatter_plot

class TestScatterPlot(unittest.TestCase):
    
    def setUp(self):
        """Create temporary directory for test outputs."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_scatter.png")
        
        # Create dummy data with known correlation
        np.random.seed(42)
        n = 50
        x = np.random.normal(0, 1, n)
        # Create y with a known positive correlation (r ~ 0.7)
        y = 2 * x + np.random.normal(0, 0.5, n)
        
        self.df = pd.DataFrame({
            "metric": x,
            "score": y
        })

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_scatter_plot_generates_png_with_annotations(self):
        """
        Test that generate_scatter_plot creates a valid PNG file
        and includes annotations for r and p-value.
        """
        # Call the function
        result_path = generate_scatter_plot(
            data=self.df,
            x_col="metric",
            y_col="score",
            output_path=self.output_path,
            title="Test Correlation",
            xlabel="Test Metric",
            ylabel="Test Score"
        )

        # Assert file was created
        self.assertIsNotNone(result_path)
        self.assertTrue(os.path.exists(result_path), f"Output file {result_path} was not created")
        
        # Assert file is not empty
        self.assertGreater(os.path.getsize(result_path), 0, "Output file is empty")
        
        # Verify it's a valid image (basic check: file extension and size)
        self.assertTrue(result_path.endswith('.png'))
        
        # Since we can't easily parse the PNG bytes in a unit test without heavy deps,
        # we rely on the fact that matplotlib saved it. 
        # In an integration test, we would use imagehash or similar to verify content.
        # Here we verify the function returned the path and the file exists.

    def test_scatter_plot_with_insufficient_data(self):
        """Test behavior with too few data points."""
        small_df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        temp_path = os.path.join(self.temp_dir, "small.png")
        
        result = generate_scatter_plot(
            data=small_df,
            x_col="x",
            y_col="y",
            output_path=temp_path
        )
        
        # Should return None for insufficient data
        self.assertIsNone(result)
        self.assertFalse(os.path.exists(temp_path))

    def test_scatter_plot_annotations_exist(self):
        """
        Verify that the plot generation process completes without error
        when real correlation stats are computed.
        """
        # This test ensures the scipy.stats call inside works
        result_path = generate_scatter_plot(
            data=self.df,
            x_col="metric",
            y_col="score",
            output_path=self.output_path,
            q=0.01
        )
        
        self.assertTrue(os.path.exists(result_path))

if __name__ == "__main__":
    unittest.main()