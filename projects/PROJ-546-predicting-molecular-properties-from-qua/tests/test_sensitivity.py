import unittest
import os
import csv
import tempfile
import shutil
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# Import the functions to test
from sensitivity_analysis import (
    load_data,
    extract_feature_importance,
    identify_top_descriptors,
    run_sensitivity_sweep,
    verify_stability,
    generate_summary_report
)

class TestSensitivityAnalysis(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.data_path = os.path.join(self.test_dir, "test_data.csv")
        self.model_path = os.path.join(self.test_dir, "test_model.pkl")
        self.output_path = os.path.join(self.test_dir, "test_output.csv")
        
        # Create dummy data
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        X = np.random.rand(n_samples, n_features)
        y = np.random.rand(n_samples) * 100  # Barrier in kcal/mol
        
        # Save to CSV
        feature_names = [f"feat_{i}" for i in range(n_features)]
        with open(self.data_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(feature_names + ["target"])
            for i in range(n_samples):
                row = list(X[i]) + [y[i]]
                writer.writerow(row)
        
        # Train and save a dummy model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Save model (using pickle)
        import pickle
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_data(self):
        X, y, names = load_data(self.data_path)
        self.assertEqual(X.shape[0], 100)
        self.assertEqual(X.shape[1], 10)
        self.assertEqual(len(names), 10)
        self.assertEqual(names[-1], "feat_9") # Last feature name

    def test_extract_feature_importance(self):
        import pickle
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        
        feature_names = [f"feat_{i}" for i in range(10)]
        importance = extract_feature_importance(model, feature_names)
        
        self.assertEqual(len(importance), 10)
        self.assertTrue(all(isinstance(v, float) for v in importance.values()))
        self.assertAlmostEqual(sum(importance.values()), 1.0, places=5)

    def test_identify_top_descriptors(self):
        import pickle
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        
        feature_names = [f"feat_{i}" for i in range(10)]
        importance = extract_feature_importance(model, feature_names)
        top_3 = identify_top_descriptors(importance, top_n=3)
        
        self.assertEqual(len(top_3), 3)
        # Check sorted descending
        for i in range(len(top_3) - 1):
            self.assertGreaterEqual(top_3[i][1], top_3[i+1][1])

    def test_run_sensitivity_sweep(self):
        import pickle
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        
        X, y, feature_names = load_data(self.data_path)
        results = run_sensitivity_sweep(X, y, feature_names, model, percentiles=[10, 50, 90])
        
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertIn("percentile", r)
            self.assertIn("mae", r)
            self.assertIn("mae_degradation", r)
            self.assertIn("num_features", r)
            self.assertGreater(r["num_features"], 0)

    def test_verify_stability(self):
        # Create results where num_features is always >= 3
        results = [
            {"num_features": 5, "percentile": 10},
            {"num_features": 4, "percentile": 50},
            {"num_features": 3, "percentile": 90}
        ]
        self.assertTrue(verify_stability(results))
        
        # Create results where one has < 3 features
        results_fail = [
            {"num_features": 5, "percentile": 10},
            {"num_features": 2, "percentile": 50},
            {"num_features": 3, "percentile": 90}
        ]
        self.assertFalse(verify_stability(results_fail))

    def test_generate_summary_report(self):
        import pickle
        with open(self.model_path, 'rb') as f:
            model = pickle.load(f)
        
        X, y, feature_names = load_data(self.data_path)
        results = run_sensitivity_sweep(X, y, feature_names, model, percentiles=[10, 50])
        
        generate_summary_report(results, self.output_path)
        
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertIn("mae_degradation", rows[0].keys())

if __name__ == "__main__":
    unittest.main()