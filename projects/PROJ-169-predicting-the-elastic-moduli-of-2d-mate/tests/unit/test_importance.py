"""
Unit tests for SHAP and Permutation Importance calculations.
"""

import unittest
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.importance import (
    calculate_shap_values,
    calculate_permutation_importance,
    _prepare_shap_inputs
)
from data_models.material_graph import MaterialGraph


class TestImportanceAnalysis(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.sample_graphs = [
            MaterialGraph(
                id="test_1",
                node_features=np.random.rand(10, 5).astype(np.float32),
                edge_features=np.random.rand(20, 3).astype(np.float32),
                edge_index=np.random.randint(0, 10, (2, 20)).astype(np.int64),
                target_moduli=np.array([150.0, 70.0, 0.3]),
                family_id="family_A"
            ),
            MaterialGraph(
                id="test_2",
                node_features=np.random.rand(8, 5).astype(np.float32),
                edge_features=np.random.rand(15, 3).astype(np.float32),
                edge_index=np.random.randint(0, 8, (2, 15)).astype(np.int64),
                target_moduli=np.array([180.0, 80.0, 0.35]),
                family_id="family_B"
            ),
            MaterialGraph(
                id="test_3",
                node_features=np.random.rand(12, 5).astype(np.float32),
                edge_features=np.random.rand(25, 3).astype(np.float32),
                edge_index=np.random.randint(0, 12, (2, 25)).astype(np.int64),
                target_moduli=np.array([120.0, 60.0, 0.25]),
                family_id="family_A"
            )
        ]

        self.temp_dir = tempfile.mkdtemp()
        self.mock_model_path = os.path.join(self.temp_dir, "mock_model.pt")
        self.mock_data_path = os.path.join(self.temp_dir, "mock_data.parquet")

        # Create a dummy model file (not used in unit tests due to mocking, but good practice)
        with open(self.mock_model_path, "w") as f:
            f.write("dummy")

    def test_prepare_shap_inputs(self):
        """Test the feature preparation logic."""
        X, y, feature_names = _prepare_shap_inputs(self.sample_graphs)

        # Check dimensions
        self.assertEqual(len(X), 3)
        self.assertEqual(X.shape[1], 5) # 5 features per node
        self.assertEqual(len(y), 3)
        self.assertEqual(len(feature_names), 5)

        # Check that y contains Young's modulus (index 0)
        expected_y = [g.target_moduli[0] for g in self.sample_graphs]
        np.testing.assert_array_almost_equal(y, expected_y)

    def test_prepare_shap_inputs_with_indices(self):
        """Test feature preparation with subset indices."""
        indices = [0, 2]
        X, y, feature_names = _prepare_shap_inputs(self.sample_graphs, indices)

        self.assertEqual(len(X), 2)
        self.assertEqual(len(y), 2)
        self.assertAlmostEqual(y[0], self.sample_graphs[0].target_moduli[0])
        self.assertAlmostEqual(y[1], self.sample_graphs[2].target_moduli[0])

    @patch('analysis.importance.shap')
    @patch('analysis.importance.create_model')
    @patch('analysis.importance.torch.load')
    def test_calculate_shap_values_structure(self, mock_torch_load, mock_create_model, mock_shap):
        """Test that SHAP calculation returns the expected structure."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.eval = MagicMock()
        mock_create_model.return_value = mock_model
        mock_torch_load.return_value = {}

        # Mock SHAP
        mock_explainer = MagicMock()
        mock_shap.KernelExplainer.return_value = mock_explainer
        # Mock shap values: (samples, features)
        mock_shap_values = np.random.rand(3, 5)
        mock_explainer.shap_values.return_value = mock_shap_values

        # Mock data loading
        with patch('analysis.importance.load_graphs_from_parquet', return_value=self.sample_graphs):
            result = calculate_shap_values(
                model_path=self.mock_model_path,
                data_path=self.mock_data_path,
                output_path=os.path.join(self.temp_dir, "shap_test.json"),
                sample_size=3,
                seed=42
            )

        # Check result structure
        self.assertIn("metadata", result)
        self.assertIn("feature_importance", result)
        self.assertIn("p_values", result)
        self.assertIn("shap_values", result)

        # Check feature_importance list
        self.assertEqual(len(result["feature_importance"]), 5)
        for item in result["feature_importance"]:
            self.assertIn("feature_name", item)
            self.assertIn("mean_abs_shap", item)
            self.assertIn("p_value", item)
            self.assertIn("rank", item)

        # Check p-values are floats
        self.assertEqual(len(result["p_values"]), 5)
        self.assertTrue(all(isinstance(p, float) for p in result["p_values"]))

    @patch('analysis.importance.torch.load')
    @patch('analysis.importance.create_model')
    def test_calculate_permutation_importance_structure(self, mock_create_model, mock_torch_load):
        """Test that permutation importance returns the expected structure."""
        # Mock model
        mock_model = MagicMock()
        mock_model.eval = MagicMock()
        mock_model.return_value = torch.tensor([1.0]) # Dummy prediction
        mock_create_model.return_value = mock_model
        mock_torch_load.return_value = {}

        # Mock the model_predict wrapper inside the function to return deterministic values
        # We need to patch the internal logic or rely on the fact that the function
        # calls model_predict which we can't easily mock without refactoring.
        # Instead, we will mock the entire function's behavior for this test
        # by patching the internal model_predict logic if possible, or just checking
        # the output structure if we can force a run.
        #
        # Given the complexity of mocking the internal loop, we will rely on
        # the fact that the function logic is straightforward and test the
        # output format by running it with a very small, controlled mock.
        #
        # Let's patch the model_predict behavior by mocking the model's forward
        # to return a constant value, so the MSE calculation is deterministic.
        import torch
        mock_model.forward = MagicMock(return_value=torch.tensor([1.0]))

        with patch('analysis.importance.load_graphs_from_parquet', return_value=self.sample_graphs):
            result = calculate_permutation_importance(
                model_path=self.mock_model_path,
                data_path=self.mock_data_path,
                output_path=os.path.join(self.temp_dir, "perm_test.json"),
                sample_size=3,
                seed=42
            )

        self.assertIn("metadata", result)
        self.assertIn("feature_importance", result)
        self.assertIn("baseline_mse", result["metadata"])

        self.assertEqual(len(result["feature_importance"]), 5)
        for item in result["feature_importance"]:
            self.assertIn("feature_name", item)
            self.assertIn("score", item)
            self.assertIn("p_value", item)


if __name__ == '__main__':
    unittest.main()