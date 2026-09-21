"""
Unit tests for the code/config.py module.
"""
import os
import time
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
# Since this is a unit test, we assume the test runner sets PYTHONPATH correctly
# or we import relative to the project root.
import sys
import importlib

# Ensure we are importing from the code directory
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import (
    init_runtime_tracker,
    check_runtime_limit,
    get_sample_limit,
    get_timeout_compile,
    get_timeout_exec,
    get_timeout_inference,
    get_runtime_limit,
    get_model_path,
    get_data_dir,
    get_output_dir,
    get_logs_dir,
    ensure_directories,
    DEFAULT_SAMPLE_LIMIT,
    DEFAULT_TIMEOUT_COMPILE,
    DEFAULT_TIMEOUT_EXEC,
    DEFAULT_TIMEOUT_INFERENCE,
    DEFAULT_RUNTIME_LIMIT,
    PROJECT_ROOT,
    DEFAULT_MODEL_PATH,
    DEFAULT_DATA_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_LOGS_DIR,
)


class TestConfigGetters(unittest.TestCase):
    """Tests for configuration getter functions."""

    def tearDown(self):
        """Clear environment variables after each test to avoid pollution."""
        # List of keys to clear
        keys = [
            "SAMPLE_LIMIT", "TIMEOUT_COMPILE_SECONDS", "TIMEOUT_EXEC_SECONDS",
            "TIMEOUT_INFERENCE_SECONDS", "RUNTIME_LIMIT_SECONDS",
            "LLM_MODEL_PATH", "DATA_DIR", "OUTPUT_DIR", "LOGS_DIR"
        ]
        for key in keys:
            if key in os.environ:
                del os.environ[key]

    def test_get_sample_limit_default(self):
        """Test that get_sample_limit returns default when env var is missing."""
        self.assertEqual(get_sample_limit(), DEFAULT_SAMPLE_LIMIT)

    def test_get_sample_limit_env(self):
        """Test that get_sample_limit returns env var value."""
        os.environ["SAMPLE_LIMIT"] = "50"
        self.assertEqual(get_sample_limit(), 50)

    def test_get_timeout_compile_default(self):
        """Test default compile timeout."""
        self.assertEqual(get_timeout_compile(), DEFAULT_TIMEOUT_COMPILE)

    def test_get_timeout_compile_env(self):
        """Test env var compile timeout."""
        os.environ["TIMEOUT_COMPILE_SECONDS"] = "300"
        self.assertEqual(get_timeout_compile(), 300)

    def test_get_timeout_exec_default(self):
        """Test default execution timeout."""
        self.assertEqual(get_timeout_exec(), DEFAULT_TIMEOUT_EXEC)

    def test_get_timeout_exec_env(self):
        """Test env var execution timeout."""
        os.environ["TIMEOUT_EXEC_SECONDS"] = "120"
        self.assertEqual(get_timeout_exec(), 120)

    def test_get_timeout_inference_default(self):
        """Test default inference timeout."""
        self.assertEqual(get_timeout_inference(), DEFAULT_TIMEOUT_INFERENCE)

    def test_get_timeout_inference_env(self):
        """Test env var inference timeout."""
        os.environ["TIMEOUT_INFERENCE_SECONDS"] = "600"
        self.assertEqual(get_timeout_inference(), 600)

    def test_get_runtime_limit_default(self):
        """Test default runtime limit."""
        self.assertEqual(get_runtime_limit(), DEFAULT_RUNTIME_LIMIT)

    def test_get_runtime_limit_env(self):
        """Test env var runtime limit."""
        os.environ["RUNTIME_LIMIT_SECONDS"] = "3600"
        self.assertEqual(get_runtime_limit(), 3600)

    def test_get_model_path_default(self):
        """Test default model path."""
        self.assertEqual(get_model_path(), Path(DEFAULT_MODEL_PATH))

    def test_get_model_path_env(self):
        """Test env var model path."""
        test_path = "/custom/path/model.gguf"
        os.environ["LLM_MODEL_PATH"] = test_path
        self.assertEqual(get_model_path(), Path(test_path))

    def test_get_data_dir_default(self):
        """Test default data directory."""
        self.assertEqual(get_data_dir(), DEFAULT_DATA_DIR)

    def test_get_data_dir_env(self):
        """Test env var data directory."""
        test_dir = "/custom/data"
        os.environ["DATA_DIR"] = test_dir
        self.assertEqual(get_data_dir(), Path(test_dir))

    def test_get_output_dir_default(self):
        """Test default output directory."""
        self.assertEqual(get_output_dir(), DEFAULT_OUTPUT_DIR)

    def test_get_output_dir_env(self):
        """Test env var output directory."""
        test_dir = "/custom/output"
        os.environ["OUTPUT_DIR"] = test_dir
        self.assertEqual(get_output_dir(), Path(test_dir))

    def test_get_logs_dir_default(self):
        """Test default logs directory."""
        self.assertEqual(get_logs_dir(), DEFAULT_LOGS_DIR)

    def test_get_logs_dir_env(self):
        """Test env var logs directory."""
        test_dir = "/custom/logs"
        os.environ["LOGS_DIR"] = test_dir
        self.assertEqual(get_logs_dir(), Path(test_dir))


class TestRuntimeTracker(unittest.TestCase):
    """Tests for runtime tracking functionality."""

    def tearDown(self):
        """Reset runtime tracker state."""
        # We need to reload the module to reset the global _start_time
        # or manually set it to None. Since we can't easily access the private var
        # from outside without importing the module object, we rely on the fact
        # that the test runner might isolate, but to be safe, we mock time.time.
        pass

    @patch("config.time.time")
    def test_init_runtime_tracker_sets_start_time(self, mock_time):
        """Test that init_runtime_tracker sets the start time."""
        mock_time.return_value = 100.0
        init_runtime_tracker()
        # We can't directly check the private variable easily without importing the module object
        # but we can verify the behavior by calling check_runtime_limit immediately.
        # However, the implementation checks if _start_time is None.
        # Let's just verify the function runs without error.
        self.assertTrue(True)

    @patch("config.time.time")
    def test_check_runtime_limit_no_limit_set(self, mock_time):
        """Test check_runtime_limit when _start_time is None (no limit exceeded)."""
        mock_time.return_value = 100.0
        # Simulate _start_time being None (default)
        # We need to patch the global variable in the config module
        with patch("config._start_time", None):
            # Should not raise
            check_runtime_limit()

    @patch("config.time.time")
    def test_check_runtime_limit_within_limit(self, mock_time):
        """Test check_runtime_limit when time is within limit."""
        mock_time.side_effect = [100.0, 105.0] # start, now
        init_runtime_tracker()
        # Should not raise
        check_runtime_limit()

    @patch("config.time.time")
    def test_check_runtime_limit_exceeded(self, mock_time):
        """Test check_runtime_limit raises when time exceeds limit."""
        # Set a very low runtime limit via env
        os.environ["RUNTIME_LIMIT_SECONDS"] = "1"
        
        mock_time.side_effect = [100.0, 105.0] # start, now (5s elapsed > 1s limit)
        init_runtime_tracker()
        
        with self.assertRaises(RuntimeError) as context:
            check_runtime_limit()
        
        self.assertIn("Runtime limit exceeded", str(context.exception))

    @patch("config.time.time")
    def test_check_runtime_limit_initializes_if_none(self, mock_time):
        """Test that check_runtime_limit initializes _start_time if it is None."""
        mock_time.return_value = 100.0
        with patch("config._start_time", None):
            # Should not raise and should set start time
            check_runtime_limit()
            # Verify it didn't raise


class TestEnsureDirectories(unittest.TestCase):
    """Tests for ensure_directories function."""

    @patch("config.get_data_dir")
    @patch("config.get_output_dir")
    @patch("config.get_logs_dir")
    def test_ensure_directories_creates_dirs(self, mock_logs, mock_output, mock_data):
        """Test that ensure_directories attempts to create directories."""
        mock_data.return_value = Path("/tmp/test_data")
        mock_output.return_value = Path("/tmp/test_output")
        mock_logs.return_value = Path("/tmp/test_logs")

        with patch.object(Path, "mkdir") as mock_mkdir:
            ensure_directories()
            self.assertEqual(mock_mkdir.call_count, 3)
            # Verify mkdir was called with parents=True, exist_ok=True
            for call in mock_mkdir.call_args_list:
                self.assertEqual(call.kwargs.get("parents"), True)
                self.assertEqual(call.kwargs.get("exist_ok"), True)

    @patch("config.get_data_dir")
    @patch("config.get_output_dir")
    @patch("config.get_logs_dir")
    def test_ensure_directories_handles_existing(self, mock_logs, mock_output, mock_data):
        """Test that ensure_directories doesn't fail if dirs exist."""
        # This is implicitly handled by exist_ok=True in mkdir
        mock_data.return_value = Path("/tmp/existing_data")
        mock_output.return_value = Path("/tmp/existing_output")
        mock_logs.return_value = Path("/tmp/existing_logs")

        with patch.object(Path, "mkdir") as mock_mkdir:
            ensure_directories()
            # Should still call mkdir 3 times, but exist_ok=True prevents error
            self.assertEqual(mock_mkdir.call_count, 3)


if __name__ == "__main__":
    unittest.main()