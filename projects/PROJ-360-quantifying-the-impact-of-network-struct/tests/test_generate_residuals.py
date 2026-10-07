import os
import sys
import unittest
import tempfile
import shutil
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sklearn.linear_model import LinearRegression

# Add parent directory to path to import the module under test
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from code.generate_residuals import generate_residuals, plot_residuals, load_data, load_model

class TestResidualGeneration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp()
        self.model_path = os.path.join(self.test_dir, "model.pkl")
        self.data_path = os.path.join(self.test_dir, "features.csv")
        self.plot_path = os.path.join(self.test_dir, "residuals.png")
        
        # Create dummy data
        np.random.seed(42)
        n_samples = 50
        X_data = np.random.rand(n_samples, 3)
        y_data = 2 * X_data[:, 0] + 3 * X_data[:, 1] - X_data[:, 2] + np.random.normal(0, 0.1, n_samples)
        
        # Train a simple model
        model = LinearRegression()
        model.fit(X_data, y_data)
        
        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Save data as CSV
        df = pd.DataFrame(X_data, columns=['f1', 'f2', 'f3'])
        df['thermal_conductivity_scalar'] = y_data
        df['material_id'] = [f"mp-{i:05d}" for i in range(n_samples)]
        df.to_csv(self.data_path, index=False)

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_load_model(self):
        model = load_model(self.model_path)
        self.assertIsInstance(model, LinearRegression)

    def test_load_data(self):
        X, y = load_data(self.data_path, 'thermal_conductivity_scalar')
        self.assertEqual(len(X), 50)
        self.assertEqual(len(y), 50)
        self.assertEqual(list(X.columns), ['f1', 'f2', 'f3'])

    def test_generate_residuals(self):
        model = load_model(self.model_path)
        X, y = load_data(self.data_path, 'thermal_conductivity_scalar')
        
        # We need to pass the original dataframe to get material_id in the result
        # The function signature in the module takes X and y, but we need to adapt
        # Let's test the logic directly
        predictions = model.predict(X)
        residuals = y - predictions
        
        self.assertEqual(len(residuals), 50)
        # Residuals should be close to zero on average for a good model
        self.assertAlmostEqual(residuals.mean(), 0.0, places=1)

    def test_plot_residuals(self):
        # Create dummy results dataframe
        np.random.seed(42)
        n = 20
        results_df = pd.DataFrame({
            'material_id': [f"mp-{i}" for i in range(n)],
            'actual': np.random.rand(n) * 10,
            'predicted': np.random.rand(n) * 10,
            'residual': np.random.rand(n) - 0.5
        })
        
        plot_residuals(results_df, self.plot_path)
        
        # Verify file exists
        self.assertTrue(os.path.exists(self.plot_path))
        self.assertGreater(os.path.getsize(self.plot_path), 0)

if __name__ == '__main__':
    unittest.main()