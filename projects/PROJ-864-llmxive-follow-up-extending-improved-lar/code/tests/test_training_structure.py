"""
Tests to verify the existence and structure of the training module.
"""
import os
import sys
import unittest
from pathlib import Path

# Add code root to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

class TestTrainingStructure(unittest.TestCase):
    """Tests for the training module structure."""

    def test_training_directory_exists(self):
        """Verify that the training directory exists."""
        training_dir = code_root / "training"
        self.assertTrue(training_dir.exists(), f"Training directory does not exist: {training_dir}")

    def test_training_init_exists(self):
        """Verify that __init__.py exists in training directory."""
        init_file = code_root / "training" / "__init__.py"
        self.assertTrue(init_file.exists(), f"__init__.py missing in training directory")

    def test_training_callbacks_exists(self):
        """Verify that callbacks.py exists."""
        callbacks_file = code_root / "training" / "callbacks.py"
        self.assertTrue(
            callbacks_file.exists(), f"callbacks.py missing in training directory"
        )

    def test_training_helpers_exists(self):
        """Verify that helpers.py exists."""
        helpers_file = code_root / "training" / "helpers.py"
        self.assertTrue(
            helpers_file.exists(), f"helpers.py missing in training directory"
        )

    def test_training_train_loop_exists(self):
        """Verify that train_loop.py exists."""
        train_loop_file = code_root / "training" / "train_loop.py"
        self.assertTrue(
            train_loop_file.exists(), f"train_loop.py missing in training directory"
        )

    def test_training_run_experiment_exists(self):
        """Verify that run_experiment.py exists."""
        run_exp_file = code_root / "training" / "run_experiment.py"
        self.assertTrue(
            run_exp_file.exists(), f"run_experiment.py missing in training directory"
        )

    def test_training_imports_work(self):
        """Verify that main modules can be imported."""
        try:
            from training.callbacks import TrainingMetrics, LoggingCallback
            from training.helpers import ensure_training_dirs
            from training.train_loop import TextDataset, train_loop
            from training.run_experiment import run_single_model_training
        except ImportError as e:
            self.fail(f"Failed to import training modules: {e}")


def run_tests():
    """Run the tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTrainingStructure)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == "__main__":
    run_tests()