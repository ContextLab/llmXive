"""
Unit tests for rule derivation logic (Task T020).
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.derive_rules import (
    extract_feature_importance,
    extract_decision_rules,
    derive_hard_thresholds,
    main
)

class TestRuleDerivation(unittest.TestCase):

    def setUp(self):
        # Create a simple mock model
        X = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0]])
        y = np.array([0, 0, 1, 1])
        self.model = DecisionTreeClassifier(max_depth=2, random_state=42)
        self.model.fit(X, y)
        self.feature_names = ["feature_a", "feature_b"]

    def test_extract_feature_importance(self):
        """Test that feature importances are extracted correctly."""
        importances = extract_feature_importance(self.model, self.feature_names)
        self.assertIsInstance(importances, dict)
        self.assertEqual(len(importances), 2)
        self.assertIn("feature_a", importances)
        self.assertIn("feature_b", importances)
        self.assertTrue(all(isinstance(v, float) for v in importances.values()))
        # Sum should be close to 1.0
        self.assertAlmostEqual(sum(importances.values()), 1.0, places=5)

    def test_extract_decision_rules(self):
        """Test that decision rules are extracted."""
        rules = extract_decision_rules(self.model, self.feature_names)
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0)
        # Check structure of rules
        for rule in rules:
            self.assertIn("type", rule)
            if rule["type"] != "leaf":
                self.assertIn("feature", rule)
                self.assertIn("operator", rule)
                self.assertIn("threshold", rule)

    def test_derive_hard_thresholds(self):
        """Test aggregation of rules from multiple models."""
        # Create two simple models
        models = [self.model, self.model]  # Use same model twice for simplicity
        thresholds = derive_hard_thresholds(models, self.feature_names)
        
        self.assertIsInstance(thresholds, dict)
        # Should have thresholds for features used by the model
        self.assertGreater(len(thresholds), 0)
        
        for feat, rule in thresholds.items():
            self.assertIn("threshold", rule)
            self.assertIn("operator", rule)
            self.assertIn("count", rule)
            self.assertIsInstance(rule["threshold"], float)
            self.assertIsInstance(rule["count"], int)

    @patch('models.derive_rules.load_models')
    @patch('models.derive_rules.pd.read_csv')
    @patch('models.derive_rules.json.dump')
    @patch('models.derive_rules.os.makedirs')
    def test_main_execution(self, mock_makedirs, mock_json_dump, mock_read_csv, mock_load_models):
        """Test the main function execution flow."""
        # Setup mocks
        mock_model = MagicMock(spec=DecisionTreeClassifier)
        mock_model.feature_importances_ = np.array([0.6, 0.4])
        mock_load_models.return_value = [mock_model, mock_model]
        
        mock_df = pd.DataFrame({"feature_a": [1, 2], "feature_b": [3, 4], "rtpurbo_label": [0, 1]})
        mock_read_csv.return_value = mock_df

        # Run main
        result = main(
            models_dir="fake_dir",
            data_path="fake_data.csv",
            output_path="fake_output.json"
        )

        self.assertEqual(result, 0)
        mock_load_models.assert_called_once()
        mock_read_csv.assert_called_once()
        mock_json_dump.assert_called_once()
        mock_makedirs.assert_called_once()

if __name__ == "__main__":
    unittest.main()