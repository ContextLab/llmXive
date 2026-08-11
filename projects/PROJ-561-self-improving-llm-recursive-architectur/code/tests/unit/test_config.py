import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import (
    Hyperparameters, SafetyConstraints, PathConfig, Config,
    get_config, set_config, get_learning_rate, get_batch_size,
    get_seed, get_ram_limit, get_trajectory_path, set_seed,
    ensure_directories, _validate_config
)

class TestConfigDefaults(unittest.TestCase):
    """Test that config loads successfully and asserts default values match spec."""

    def test_hyperparameters_defaults(self):
        """Verify hyperparameters match specification."""
        hp = Hyperparameters()
        self.assertEqual(hp.learning_rate, 5e-5)
        self.assertEqual(hp.batch_size, 4)
        self.assertIsNotNone(hp.seed)
        self.assertEqual(hp.gradient_accumulation_steps, 4)

    def test_safety_constraints_defaults(self):
        """Verify safety constraints match specification."""
        sc = SafetyConstraints()
        self.assertEqual(sc.max_param_increase_ratio, 1.30)
        self.assertEqual(sc.max_ram_gb, 7.0)
        self.assertEqual(sc.max_attempts, 3)
        self.assertEqual(sc.early_stop_degradation_threshold, 0.05)

    def test_get_config_returns_singleton(self):
        """Verify get_config returns a consistent instance."""
        cfg1 = get_config()
        cfg2 = get_config()
        self.assertIs(cfg1, cfg2)

    def test_get_learning_rate(self):
        """Verify get_learning_rate returns correct value."""
        self.assertEqual(get_learning_rate(), 5e-5)

    def test_get_batch_size(self):
        """Verify get_batch_size returns correct value."""
        self.assertEqual(get_batch_size(), 4)

    def test_get_ram_limit(self):
        """Verify get_ram_limit returns correct value."""
        self.assertEqual(get_ram_limit(), 7.0)

    def test_get_trajectory_path(self):
        """Verify get_trajectory_path returns expected path."""
        path = get_trajectory_path()
        self.assertIn("results", path)
        self.assertIn("trajectory.json", path)

    def test_set_seed(self):
        """Verify set_seed sets random seeds correctly."""
        set_seed(123)
        self.assertEqual(get_seed(), 123)

    def test_ensure_directories(self):
        """Verify ensure_directories creates required directories."""
        # Create a temporary root for testing
        import tempfile
        import shutil
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the paths to use temp directory
            original_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # We need to patch the PathConfig to use our temp dir
            # This is a bit complex, so we'll just test that the function runs without error
            # and creates directories in the expected locations relative to the project root
            try:
                ensure_directories()
                # Check that directories exist (relative to actual project root)
                config = get_config()
                self.assertTrue(os.path.exists(config.paths.data_raw))
                self.assertTrue(os.path.exists(config.paths.results))
            except Exception as e:
                self.fail(f"ensure_directories raised an exception: {e}")

    def test_validation_on_import(self):
        """Verify that _validate_config does not raise on valid defaults."""
        # This should not raise any AssertionError
        try:
            _validate_config()
        except AssertionError as e:
            self.fail(f"Validation failed on valid defaults: {e}")

if __name__ == '__main__':
    unittest.main()