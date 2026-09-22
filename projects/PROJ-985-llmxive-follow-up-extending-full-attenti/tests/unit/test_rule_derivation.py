"""
Unit tests for rule derivation logic (Task T017).

This module tests the logic in `code/models/derive_rules.py` which extracts
hard thresholds from trained model importance scores.
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock, mock_open

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
        # Create a simple mock model for testing logic
        # Feature 0: Entropy, Feature 1: KenLM Perplexity
        X = np.array([
            [1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0],
            [1.5, 2.5], [2.5, 3.5], [3.5, 4.5], [4.5, 5.5]
        ])
        y = np.array([0, 0, 1, 1, 0, 0, 1, 1])
        self.model = DecisionTreeClassifier(max_depth=3, random_state=42)
        self.model.fit(X, y)
        self.feature_names = ["entropy", "kenlm_perplexity"]

    def test_extract_feature_importance(self):
        """Test that feature importances are extracted correctly."""
        importances = extract_feature_importance(self.model, self.feature_names)
        
        self.assertIsInstance(importances, dict)
        self.assertEqual(len(importances), 2)
        self.assertIn("entropy", importances)
        self.assertIn("kenlm_perplexity", importances)
        
        # Values should be floats
        self.assertTrue(all(isinstance(v, float) for v in importances.values()))
        
        # Sum of importances should be close to 1.0
        self.assertAlmostEqual(sum(importances.values()), 1.0, places=5)

    def test_extract_decision_rules(self):
        """Test that decision rules are extracted from the tree."""
        rules = extract_decision_rules(self.model, self.feature_names)
        
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0)
        
        # Check structure of rules
        for rule in rules:
            self.assertIn("type", rule)
            if rule["type"] != "leaf":
                # Internal node rules
                self.assertIn("feature", rule)
                self.assertIn("operator", rule)
                self.assertIn("threshold", rule)
                self.assertIn("value_if_true", rule) # e.g., "left" or "right"
            else:
                # Leaf node rules
                self.assertIn("value", rule)
                self.assertIn("samples", rule)

    def test_derive_hard_thresholds(self):
        """Test aggregation of rules from multiple models."""
        # Create two simple models with slightly different data
        models = [self.model]
        # Create a second model with a different random seed to vary tree structure slightly
        X2 = np.array([
            [1.1, 2.1], [2.1, 3.1], [3.1, 4.1], [4.1, 5.1],
            [1.4, 2.4], [2.4, 3.4], [3.4, 4.4], [4.4, 5.4]
        ])
        model2 = DecisionTreeClassifier(max_depth=3, random_state=123)
        model2.fit(X2, np.array([0, 0, 1, 1, 0, 0, 1, 1]))
        models.append(model2)

        thresholds = derive_hard_thresholds(models, self.feature_names)
        
        self.assertIsInstance(thresholds, dict)
        # Should have thresholds for features used by the models
        self.assertGreater(len(thresholds), 0)
        
        for feat, rule in thresholds.items():
            self.assertIn("threshold", rule)
            self.assertIn("operator", rule)
            self.assertIn("count", rule)
            self.assertIsInstance(rule["threshold"], float)
            self.assertIsInstance(rule["count"], int)
            # Count should be at least 1 since we passed 2 models
            self.assertGreaterEqual(rule["count"], 1)

    @patch('models.derive_rules.load_models')
    @patch('models.derive_rules.pd.read_csv')
    @patch('builtins.open', new_callable=mock_open)
    @patch('models.derive_rules.os.makedirs')
    def test_main_execution(self, mock_makedirs, mock_file, mock_read_csv, mock_load_models):
        """Test the main function execution flow."""
        # Setup mocks
        mock_model = MagicMock(spec=DecisionTreeClassifier)
        mock_model.feature_importances_ = np.array([0.6, 0.4])
        mock_model.tree_ = self.model.tree_ # Attach real tree structure for rule extraction logic
        mock_load_models.return_value = [mock_model]
        
        mock_df = pd.DataFrame({
            "entropy": [1.0, 2.0], 
            "kenlm_perplexity": [3.0, 4.0], 
            "rtpurbo_label": [0, 1]
        })
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
        mock_makedirs.assert_called_once()
        # Verify file write was attempted
        mock_file.assert_called()

if __name__ == "__main__":
    unittest.main()