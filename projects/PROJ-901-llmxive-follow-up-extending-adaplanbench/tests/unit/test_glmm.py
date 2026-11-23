"""
Unit tests for GLMM model fitting (T028).
Performs a sanity check on synthetic data to ensure the model fitting logic works.
"""
import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.glmm import (
    load_execution_traces,
    prepare_data_for_glmm,
    fit_glmm,
    calculate_effect_sizes,
    run_statistical_analysis
)
from config import ensure_directories

class TestGLMMFitting(unittest.TestCase):
    """Unit tests for GLMM model fitting on synthetic data."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_input_path = os.path.join(self.temp_dir, "test_execution_traces.csv")
        self.test_output_path = os.path.join(self.temp_dir, "test_statistical_results.json")
        ensure_directories()

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_input_path):
            os.remove(self.test_input_path)
        if os.path.exists(self.test_output_path):
            os.remove(self.test_output_path)

    def _create_synthetic_traces(self, rows: int = 100, architecture_split: float = 0.5):
        """
        Create a synthetic execution_traces.csv file for testing.
        
        Args:
            rows: Number of rows to generate
            architecture_split: Proportion of 'dual_track' vs 'monolithic'
        """
        import pandas as pd
        import random
        
        random.seed(42)
        
        data = []
        for i in range(rows):
            task_id = f"task_{i:04d}"
            # Split architectures
            if random.random() < architecture_split:
                architecture = "dual_track"
            else:
                architecture = "monolithic"
            
            # Constraint count: 5 to 10
            constraint_count = random.randint(5, 10)
            
            # Generate a violation status based on architecture and constraint count
            # Dual track should have fewer violations, especially at high constraint counts
            base_violation_prob = 0.3
            if architecture == "dual_track":
                base_violation_prob = 0.15
            
            # Increase probability with constraint count
            violation_prob = base_violation_prob + (constraint_count - 5) * 0.02
            
            violation_boolean = random.random() < violation_prob
            violation_reason = "constraint_violation" if violation_boolean else None
            
            # Violation status: mostly null, some specific cases
            if violation_boolean:
                violation_status = random.choice([None, "false_negative", "implicit_unverified"])
            else:
                violation_status = None
            
            # Final score: 0.0 to 1.0, correlated with violations
            if violation_boolean:
                final_score = random.uniform(0.0, 0.6)
            else:
                final_score = random.uniform(0.7, 1.0)
            
            data.append({
                "task_id": task_id,
                "architecture": architecture,
                "constraint_count": constraint_count,
                "violation_boolean": violation_boolean,
                "violation_reason": violation_reason,
                "violation_status": violation_status,
                "final_score": final_score
            })
        
        df = pd.DataFrame(data)
        df.to_csv(self.test_input_path, index=False)
        return df

    def test_load_execution_traces(self):
        """Test loading execution traces from CSV."""
        df = self._create_synthetic_traces(50)
        
        loaded_df = load_execution_traces(self.test_input_path)
        
        self.assertEqual(len(loaded_df), 50)
        self.assertIn("task_id", loaded_df.columns)
        self.assertIn("architecture", loaded_df.columns)
        self.assertIn("constraint_count", loaded_df.columns)
        self.assertIn("violation_boolean", loaded_df.columns)
        self.assertIn("final_score", loaded_df.columns)

    def test_prepare_data_for_glmm(self):
        """Test data preparation for GLMM."""
        df = self._create_synthetic_traces(100)
        
        prepared_data = prepare_data_for_glmm(df)
        
        # Check that binary outcome is created
        self.assertIn("outcome", prepared_data.columns)
        self.assertIn("architecture_encoded", prepared_data.columns)
        self.assertIn("constraint_count", prepared_data.columns)
        
        # Check that outcome is binary (0 or 1)
        self.assertTrue(all(prepared_data["outcome"].isin([0, 1])))
        
        # Check that architecture is encoded
        self.assertTrue(all(prepared_data["architecture_encoded"].isin([0, 1])))

    def test_fit_glmm(self):
        """Test GLMM model fitting."""
        df = self._create_synthetic_traces(200)
        
        prepared_data = prepare_data_for_glmm(df)
        
        # Fit the model
        model, results = fit_glmm(prepared_data)
        
        # Check that results contain expected fields
        self.assertIn("coefficients", results)
        self.assertIn("p_values", results)
        self.assertIn("interaction_p_value", results)
        
        # Check that coefficients are present
        self.assertIn("architecture_encoded", results["coefficients"])
        self.assertIn("constraint_count", results["coefficients"])
        self.assertIn("architecture_encoded:constraint_count", results["coefficients"])
        
        # Check that p-values are valid numbers
        self.assertIsInstance(results["p_values"]["architecture_encoded"], float)
        self.assertIsInstance(results["p_values"]["constraint_count"], float)
        self.assertIsInstance(results["p_values"]["interaction_p_value"], float)

    def test_calculate_effect_sizes(self):
        """Test effect size calculation."""
        df = self._create_synthetic_traces(200)
        
        prepared_data = prepare_data_for_glmm(df)
        model, glmm_results = fit_glmm(prepared_data)
        
        effect_sizes = calculate_effect_sizes(prepared_data, glmm_results)
        
        self.assertIn("cohen_f_squared", effect_sizes)
        self.assertIn("interaction_effect_size", effect_sizes)
        
        # Check that effect sizes are non-negative
        self.assertGreaterEqual(effect_sizes["cohen_f_squared"], 0)
        self.assertGreaterEqual(effect_sizes["interaction_effect_size"], 0)

    def test_run_statistical_analysis(self):
        """Test full statistical analysis pipeline."""
        df = self._create_synthetic_traces(300)
        
        results = run_statistical_analysis(self.test_input_path, self.test_output_path)
        
        # Check that results file was written
        self.assertTrue(os.path.exists(self.test_output_path))
        
        # Check that results contain expected fields
        with open(self.test_output_path, 'r') as f:
            saved_results = json.load(f)
        
        self.assertIn("interaction_p_value", saved_results)
        self.assertIn("interaction_coefficient", saved_results)
        self.assertIn("cohen_f_squared", saved_results)
        self.assertIn("model_converged", saved_results)
        
        # Check that p-value is a valid number
        self.assertIsInstance(saved_results["interaction_p_value"], float)
        self.assertGreater(saved_results["interaction_p_value"], 0)
        self.assertLess(saved_results["interaction_p_value"], 1)

    def test_interaction_effect_detection(self):
        """Test that the model can detect an interaction effect when present."""
        # Create data with a clear interaction effect
        rows = 500
        data = []
        
        for i in range(rows):
            task_id = f"task_{i:04d}"
            architecture = "dual_track" if i < rows // 2 else "monolithic"
            constraint_count = random.randint(5, 10)
            
            # Strong interaction: dual track maintains high scores even at high constraints
            # monolithic scores drop significantly at high constraints
            if architecture == "dual_track":
                base_score = 0.9 - (constraint_count - 5) * 0.02
            else:
                base_score = 0.9 - (constraint_count - 5) * 0.12
            
            final_score = max(0.0, min(1.0, base_score + random.uniform(-0.1, 0.1)))
            violation_boolean = 0 if final_score > 0.7 else 1
            
            data.append({
                "task_id": task_id,
                "architecture": architecture,
                "constraint_count": constraint_count,
                "violation_boolean": violation_boolean,
                "violation_reason": "constraint_violation" if violation_boolean else None,
                "violation_status": None,
                "final_score": final_score
            })
        
        import pandas as pd
        df = pd.DataFrame(data)
        df.to_csv(self.test_input_path, index=False)
        
        results = run_statistical_analysis(self.test_input_path, self.test_output_path)
        
        # The interaction effect should be detectable (p < 0.05)
        self.assertLess(results["interaction_p_value"], 0.05, 
                      "Interaction effect should be significant in this synthetic data")

    def test_empty_dataset_handling(self):
        """Test handling of empty dataset."""
        import pandas as pd
        empty_df = pd.DataFrame(columns=["task_id", "architecture", "constraint_count", 
                                        "violation_boolean", "violation_reason", 
                                        "violation_status", "final_score"])
        empty_df.to_csv(self.test_input_path, index=False)
        
        with self.assertRaises(ValueError):
            run_statistical_analysis(self.test_input_path, self.test_output_path)

    def test_single_architecture_handling(self):
        """Test handling of dataset with only one architecture type."""
        df = self._create_synthetic_traces(100, architecture_split=1.0)
        
        # All should be dual_track
        self.assertTrue(all(df["architecture"] == "dual_track"))
        
        # This should still run but may not have a meaningful interaction effect
        results = run_statistical_analysis(self.test_input_path, self.test_output_path)
        
        # Should still produce valid results
        self.assertIn("interaction_p_value", results)
        self.assertIsInstance(results["interaction_p_value"], float)

if __name__ == "__main__":
    unittest.main()