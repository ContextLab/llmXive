"""Unit tests for memory_enforcer module."""
import gc
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from model.memory_enforcer import (
    MAX_MEMORY_GB,
    enforce_memory_limit,
    get_memory_peak_mb,
    run_training_with_memory_enforcement,
)


class TestMemoryEnforcer(unittest.TestCase):
    """Tests for memory enforcement logic."""

    def test_get_memory_peak_mb(self):
        """Test that memory peak is measured correctly."""
        tracemalloc = None
        try:
            import tracemalloc
            tracemalloc.start()
            _ = torch.randn(100000)
            peak_mb = get_memory_peak_mb()
            self.assertGreater(peak_mb, 0)
        finally:
            if tracemalloc:
                tracemalloc.stop()

    def test_enforce_memory_limit_success(self):
        """Test successful epoch execution within memory limit."""
        def dummy_epoch(batch_size: int) -> None:
            # Small allocation that should fit
            _ = torch.randn(batch_size * 100)

        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test_log.json")
            final_bs, peak_gb, log = enforce_memory_limit(
                dummy_epoch,
                initial_batch_size=64,
                min_batch_size=1,
                max_memory_gb=MAX_MEMORY_GB,
                output_log_path=log_path,
            )

            self.assertEqual(final_bs, 64)
            self.assertLess(peak_gb, MAX_MEMORY_GB)
            self.assertEqual(log["status"], "success")

            # Verify log file was written
            self.assertTrue(os.path.exists(log_path))
            with open(log_path, "r") as f:
                data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)

    def test_enforce_memory_limit_reduction(self):
        """Test batch size reduction when memory is exceeded."""
        # Simulate a function that consumes memory based on batch size
        # We'll mock the memory measurement to force a reduction
        call_count = 0

        def mock_epoch(batch_size: int) -> None:
            nonlocal call_count
            call_count += 1
            # Just a placeholder; real memory is mocked below

        with patch("model.memory_enforcer.tracemalloc") as mock_tracemalloc:
            # First call: high memory (exceeds limit)
            # Second call: low memory (within limit)
            mock_tracemalloc.get_traced_memory.side_effect = [
                (0, 8 * 1024 * 1024 * 1024),  # 8 GB (exceeds 7 GB)
                (0, 4 * 1024 * 1024 * 1024),  # 4 GB (within limit)
            ]
            mock_tracemalloc.start = lambda: None
            mock_tracemalloc.stop = lambda: None

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "test_log.json")
                final_bs, peak_gb, log = enforce_memory_limit(
                    mock_epoch,
                    initial_batch_size=64,
                    min_batch_size=1,
                    max_memory_gb=7.0,
                    output_log_path=log_path,
                )

                # Should have reduced batch size
                self.assertLess(final_bs, 64)
                self.assertEqual(log["reduction_steps"], 1)

    def test_enforce_memory_limit_failure(self):
        """Test SystemExit when memory limit exceeded at min batch size."""
        def high_memory_epoch(batch_size: int) -> None:
            # Always consume too much memory
            pass

        with patch("model.memory_enforcer.tracemalloc") as mock_tracemalloc:
            mock_tracemalloc.get_traced_memory.return_value = (0, 10 * 1024 * 1024 * 1024)  # 10 GB
            mock_tracemalloc.start = lambda: None
            mock_tracemalloc.stop = lambda: None

            with tempfile.TemporaryDirectory() as tmpdir:
                log_path = os.path.join(tmpdir, "test_log.json")
                with self.assertRaises(SystemExit) as ctx:
                    enforce_memory_limit(
                        high_memory_epoch,
                        initial_batch_size=1,  # Start at min
                        min_batch_size=1,
                        max_memory_gb=7.0,
                        output_log_path=log_path,
                    )

                self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()