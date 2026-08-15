import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import psutil
import logging
from io import StringIO

# Add project root to path if running from tests directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.memory import check_ram_usage, get_memory_usage_gb, check_and_terminate_if_exceeds, enforce_ram_limit
import torch.nn as nn
import torch


class TestMemoryWatchdogT004(unittest.TestCase):
    """Unit tests specifically for T004: check_ram_usage warning logic."""

    def setUp(self):
        # Setup a string handler to capture log output
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.handler.setLevel(logging.WARNING)
        self.logger = logging.getLogger('utils.memory')
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.WARNING)

    def tearDown(self):
        self.logger.removeHandler(self.handler)

    @patch('utils.memory.psutil.Process')
    def test_check_ram_usage_below_limit(self, mock_process_class):
        """Verify no warning is logged when usage is below limit."""
        mock_process = MagicMock()
        # Mock RSS to be 2.0 GB
        mock_process.memory_info.return_value.rss = 2.0 * 1024**3
        mock_process_class.return_value = mock_process

        result = check_ram_usage(limit_gb=6.8)
        
        self.assertTrue(result, "check_ram_usage should return True when usage < limit")
        self.assertEqual(self.log_stream.getvalue(), "", "No warning should be logged")

    @patch('utils.memory.psutil.Process')
    def test_check_ram_usage_exceeds_limit_logs_warning(self, mock_process_class):
        """Verify warning is logged when usage exceeds limit, but no exception is raised."""
        mock_process = MagicMock()
        # Mock RSS to be 7.0 GB (exceeds 6.8)
        mock_process.memory_info.return_value.rss = 7.0 * 1024**3
        mock_process_class.return_value = mock_process

        # This should NOT raise an exception
        try:
            result = check_ram_usage(limit_gb=6.8)
            success = True
        except Exception:
            success = False

        self.assertTrue(success, "check_ram_usage should NOT raise an exception on high usage")
        self.assertFalse(result, "check_ram_usage should return False when usage >= limit")
        
        log_output = self.log_stream.getvalue()
        self.assertIn("RAM Critical", log_output, "Log should contain 'RAM Critical'")
        self.assertIn("7.00", log_output, "Log should contain usage value")

    @patch('utils.memory.psutil.Process')
    def test_check_ram_usage_at_limit(self, mock_process_class):
        """Verify behavior when usage is exactly at the limit (should log warning)."""
        mock_process = MagicMock()
        # Mock RSS to be exactly 6.8 GB
        mock_process.memory_info.return_value.rss = 6.8 * 1024**3
        mock_process_class.return_value = mock_process

        result = check_ram_usage(limit_gb=6.8)
        
        # The logic is `if current_usage >= limit_gb`, so at exact limit it triggers
        self.assertFalse(result, "Should return False at exact limit")
        
        log_output = self.log_stream.getvalue()
        self.assertIn("RAM Critical", log_output)


class TestMemoryWatchdog(unittest.TestCase):
    """Unit tests for the memory watchdog and safety functions in utils.memory."""

    def test_get_memory_usage_gb_returns_float(self):
        """Verify get_memory_usage_gb returns a positive float."""
        usage = get_memory_usage_gb()
        self.assertIsInstance(usage, float)
        self.assertGreater(usage, 0.0)

    @patch('utils.memory.psutil.Process')
    def test_check_and_terminate_below_limit(self, mock_process_class):
        """Verify no termination occurs when memory is below limit."""
        mock_process = MagicMock()
        # Mock RSS to be 2.0 GB
        mock_process.memory_info.return_value.rss = 2.0 * 1024**3
        mock_process_class.return_value = mock_process

        # This should NOT raise SystemExit
        try:
            check_and_terminate_if_exceeds(limit_gb=5.0)
            success = True
        except SystemExit:
            success = False

        self.assertTrue(success, "check_and_terminate_if_exceeds should not exit when usage < limit")

    @patch('utils.memory.psutil.Process')
    def test_check_and_terminate_exceeds_limit(self, mock_process_class):
        """Verify SystemExit is raised when memory exceeds limit."""
        mock_process = MagicMock()
        # Mock RSS to be 8.0 GB
        mock_process.memory_info.return_value.rss = 8.0 * 1024**3
        mock_process_class.return_value = mock_process

        # This MUST raise SystemExit
        with self.assertRaises(SystemExit) as context:
            check_and_terminate_if_exceeds(limit_gb=5.0)

        # Verify the exit code is non-zero
        self.assertNotEqual(context.exception.code, 0)
        
        # Verify the process was queried
        mock_process_class.assert_called_once()
        mock_process.memory_info.assert_called_once()

    @patch('utils.memory.psutil.Process')
    def test_check_and_terminate_at_exact_limit(self, mock_process_class):
        """Verify behavior when memory is exactly at the limit (should NOT exit)."""
        mock_process = MagicMock()
        # Mock RSS to be exactly 5.0 GB
        mock_process.memory_info.return_value.rss = 5.0 * 1024**3
        mock_process_class.return_value = mock_process

        # Should NOT exit at exactly the limit (logic is > limit)
        try:
            check_and_terminate_if_exceeds(limit_gb=5.0)
            success = True
        except SystemExit:
            success = False

        self.assertTrue(success, "Should not exit when usage == limit")

    @patch('utils.memory.psutil.Process')
    def test_enforce_ram_limit_exceeds(self, mock_process_class):
        """Verify enforce_ram_limit terminates on exceedance."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 8.0 * 1024**3
        mock_process_class.return_value = mock_process

        with self.assertRaises(SystemExit):
            enforce_ram_limit(limit_gb=5.0)

    @patch('utils.memory.psutil.Process')
    def test_enforce_ram_limit_safe(self, mock_process_class):
        """Verify enforce_ram_limit does nothing if safe."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 2.0 * 1024**3
        mock_process_class.return_value = mock_process

        try:
            enforce_ram_limit(limit_gb=5.0)
            success = True
        except SystemExit:
            success = False
        
        self.assertTrue(success)


class TestGradientCheckpointing(unittest.TestCase):
    """Unit tests for gradient checkpointing utility."""

    def test_enable_gradient_checkpointing_on_empty_model(self):
        """Verify function handles models with no parameters gracefully."""
        class EmptyModel(nn.Module):
            def __init__(self):
                super().__init__()
        
        model = EmptyModel()
        # Should not raise
        result = enable_gradient_checkpointing(model)
        self.assertIsNone(result)

    def test_enable_gradient_checkpointing_on_standard_model(self):
        """Verify gradient checkpointing is enabled on a standard model."""
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 10)
            
            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()
        
        # Mock the model's gradient_checkpointing_enable method
        model.gradient_checkpointing_enable = MagicMock()
        
        result = enable_gradient_checkpointing(model)
        
        model.gradient_checkpointing_enable.assert_called_once()
        self.assertIsNone(result)

    def test_enable_gradient_checkpointing_no_method(self):
        """Verify function handles models without the method gracefully."""
        class SimpleModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = nn.Linear(10, 10)
            
            def forward(self, x):
                return self.linear(x)

        model = SimpleModel()
        # Ensure the method doesn't exist
        if hasattr(model, 'gradient_checkpointing_enable'):
            delattr(model, 'gradient_checkpointing_enable')
        
        # Should not raise
        result = enable_gradient_checkpointing(model)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()