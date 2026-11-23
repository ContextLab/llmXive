"""
Integration test for the model training and evaluation pipeline.

This test verifies that:
1. models/train.py executes successfully and produces output files.
2. models/evaluate.py executes successfully using the training outputs.
3. The resulting output files (training_metrics.json, evaluation_results.json)
   exist and contain valid JSON.
"""
import os
import sys
import json
import subprocess
import unittest
from pathlib import Path

# Add the project root to the path to allow imports if running as a script,
# though we will invoke via python -m or subprocess for isolation.
project_root = Path(__file__).resolve().parent.parent
code_root = project_root / "code"

if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import get_models_dir, get_processed_dir


class TestIntegrationPipeline(unittest.TestCase):
    """Integration tests for the ML pipeline."""

    def setUp(self):
        """Ensure we have the correct directories."""
        self.models_dir = get_models_dir()
        self.processed_dir = get_processed_dir()
        
        # Paths for expected outputs
        self.training_metrics_path = self.models_dir / "training_metrics.json"
        self.evaluation_results_path = self.models_dir / "evaluation_results.json"
        self.model_path = self.models_dir / "random_forest.pkl"
        
        # Clean up any previous run artifacts to ensure fresh execution
        for path in [self.training_metrics_path, self.evaluation_results_path, self.model_path]:
            if path.exists():
                path.unlink()

    def test_train_and_evaluate_pipeline(self):
        """
        Run models/train.py then models/evaluate.py and verify outputs.
        """
        # 1. Run training script
        train_script = code_root / "models" / "train.py"
        train_cmd = [sys.executable, str(train_script)]
        
        train_result = subprocess.run(
            train_cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        if train_result.returncode != 0:
            self.fail(
                f"Training script failed.\nSTDOUT:\n{train_result.stdout}\n"
                f"STDERR:\n{train_result.stderr}"
            )
        
        # 2. Verify training outputs exist and are valid JSON
        self.assertTrue(
            self.training_metrics_path.exists(),
            f"Training metrics file not found: {self.training_metrics_path}"
        )
        
        try:
            with open(self.training_metrics_path, 'r') as f:
                training_data = json.load(f)
            self.assertIsInstance(training_data, dict, "Training metrics must be a JSON object")
            self.assertIn("model_type", training_data, "Training metrics missing 'model_type'")
            self.assertIn("cv_metrics", training_data, "Training metrics missing 'cv_metrics'")
        except json.JSONDecodeError as e:
            self.fail(f"Training metrics file is not valid JSON: {e}")
        
        # 3. Run evaluation script
        eval_script = code_root / "models" / "evaluate.py"
        eval_cmd = [sys.executable, str(eval_script)]
        
        eval_result = subprocess.run(
            eval_cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True
        )
        
        if eval_result.returncode != 0:
            self.fail(
                f"Evaluation script failed.\nSTDOUT:\n{eval_result.stdout}\n"
                f"STDERR:\n{eval_result.stderr}"
            )
        
        # 4. Verify evaluation outputs exist and are valid JSON
        self.assertTrue(
            self.evaluation_results_path.exists(),
            f"Evaluation results file not found: {self.evaluation_results_path}"
        )
        
        try:
            with open(self.evaluation_results_path, 'r') as f:
                eval_data = json.load(f)
            self.assertIsInstance(eval_data, dict, "Evaluation results must be a JSON object")
            self.assertIn("balanced_accuracy", eval_data, "Evaluation results missing 'balanced_accuracy'")
            self.assertIn("p_value", eval_data, "Evaluation results missing 'p_value'")
            self.assertIn("pass_fail_flag", eval_data, "Evaluation results missing 'pass_fail_flag'")
        except json.JSONDecodeError as e:
            self.fail(f"Evaluation results file is not valid JSON: {e}")

    def test_model_artifact_exists(self):
        """Verify that the trained model pickle file exists."""
        model_path = self.models_dir / "random_forest.pkl"
        self.assertTrue(
            model_path.exists(),
            f"Trained model file not found: {model_path}"
        )
        # Verify it's not empty
        self.assertGreater(
            model_path.stat().st_size,
            0,
            "Trained model file is empty"
        )


if __name__ == '__main__':
    unittest.main()