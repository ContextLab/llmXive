"""
Unit tests for deterministic logging and seed management (T004).
"""
import os
import random
import logging
import tempfile
import shutil

import pytest

# Mock numpy/torch if not present to avoid import errors in test env
# The module handles missing imports gracefully, but we test the logic path.
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from code.utils.logging import set_seeds, get_logger, DEFAULT_SEED, LOG_DIR


class TestSeedManagement:
    """Tests for set_seeds and get_seed functionality."""

    def test_set_seeds_python_random(self):
        """Verify Python random seed is set correctly."""
        seed_val = 12345
        set_seeds(seed_val)
        val1 = random.random()

        # Reset and check reproducibility
        set_seeds(seed_val)
        val2 = random.random()

        assert val1 == val2, "Python random seed not reproducible"

    def test_set_seeds_numpy(self):
        """Verify NumPy random seed is set correctly if available."""
        if not HAS_NUMPY:
            pytest.skip("NumPy not installed")

        seed_val = 54321
        set_seeds(seed_val)
        arr1 = np.random.rand(5)

        set_seeds(seed_val)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2), "NumPy random seed not reproducible"

    def test_set_seeds_torch(self):
        """Verify PyTorch random seed is set correctly if available."""
        if not HAS_TORCH:
            pytest.skip("PyTorch not installed")

        seed_val = 99999
        set_seeds(seed_val)
        t1 = torch.rand(5)

        set_seeds(seed_val)
        t2 = torch.rand(5)

        assert torch.equal(t1, t2), "PyTorch random seed not reproducible"

    def test_get_seed_default(self):
        """Verify default seed is returned if env var is not set."""
        # Ensure env var is not set
        if "HEA_SEED" in os.environ:
            del os.environ["HEA_SEED"]

        seed = get_seed()
        assert seed == DEFAULT_SEED, f"Expected default seed {DEFAULT_SEED}, got {seed}"

    def test_get_seed_env_override(self):
        """Verify seed is read from environment variable."""
        custom_seed = 77777
        os.environ["HEA_SEED"] = str(custom_seed)
        seed = get_seed()
        assert seed == custom_seed, f"Expected seed {custom_seed}, got {seed}"
        del os.environ["HEA_SEED"]


class TestLogger:
    """Tests for get_logger functionality."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create a temporary directory for logs and clean up after."""
        self.temp_dir = tempfile.mkdtemp()
        # Temporarily override LOG_DIR for the test
        self.original_log_dir = LOG_DIR
        # We can't easily change the global LOG_DIR in the module without import reload,
        # so we will just ensure the log directory exists and is writable.
        # The actual file path logic is tested by checking if a log file is created.
        yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_creation(self):
        """Verify a logger is created and handlers are added."""
        logger = get_logger("test_logger", seed=42, log_to_file=False)
        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_logger_reproducibility_seed(self):
        """Verify that creating a logger sets the seed."""
        seed_val = 88888
        # Reset seed to something else first
        set_seeds(0)
        val_before = random.random()

        logger = get_logger("test_seed_logger", seed=seed_val, log_to_file=False)

        # Get a new random value
        val_after = random.random()

        # Reset and generate again to confirm the seed was set
        set_seeds(seed_val)
        val_check = random.random()

        # The second call after logger creation should match the check
        assert val_after == val_check, "Logger creation should have set the seed"

    def test_logger_file_creation(self):
        """Verify that a log file is created when log_to_file=True."""
        # We rely on the module's LOG_DIR. We just check that a file appears.
        # To avoid clutter, we use a specific seed and check the file existence.
        test_seed = 11111
        logger = get_logger("test_file_logger", seed=test_seed, log_to_file=True)

        # The log file should be created in output/logs
        # We check if any log file exists in that directory (since timestamp varies)
        if os.path.exists(LOG_DIR):
            files = [f for f in os.listdir(LOG_DIR) if f.startswith(f"run_seed_{test_seed}")]
            assert len(files) > 0, "Log file was not created"
        else:
            # If directory doesn't exist, that's a failure of the function
            assert False, "Log directory was not created"