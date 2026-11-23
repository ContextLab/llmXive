import unittest
from code.analyze_results import load_simulation_data, validate_sample_size, run_logistic_regression
import numpy as np
import json

class TestAnalyzeResults(unittest.TestCase):

    def test_load_simulation_data(self):
        # Create a dummy data file
        data = [{"density": 0.5, "horizon": 2, "success": 1}, {"density": 0.2, "horizon": 5, "success": 0}]
        with open("test_data.json", "w") as f:
            json.dump(data, f)

        # Load the data
        loaded_data = load_simulation_data("test_data.json")
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["density"], 0.5)

    def test_validate_sample_size(self):
        sample_size = validate_sample_size()
        self.assertIsInstance(sample_size, int)
        self.assertGreater(sample_size, 0)

    def test_run_logistic_regression(self):
      # Create some dummy data
      data = [{"density": 0.5, "horizon": 2, "success": 1}, {"density": 0.2, "horizon": 5, "success": 0}]
      X = np.array([d['density'] for d in data])
      horizon = np.array([d['horizon'] for d in data])
      y = np.array([d['success'] for d in data])

      # Run the regression
      result = run_logistic_regression(data, "density * horizon")

      # Check that the result is not None
      self.assertIsNotNone(result)
      self.assertIsInstance(result, type(sm.LogitResult()))
