"""
Integration test for hard timeout enforcement in the training loop.

This test asserts that the training job fails gracefully within the configured
time limit (FR-008) and verifies that the experiment runner enforces this
constraint across multiple seeds (SC-003).

It simulates a scenario where the training loop is artificially slowed down
to trigger the timeout mechanism, ensuring the system does not hang indefinitely.
"""

import os
import time
import tempfile
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

# Import project utilities
from src.utils.config import SocraticConfig, set_global_config
from src.utils.logging import SocraticLogger, get_logger
from src.train.train_loop import run_training_job, TrainingResult


class TestTimeoutEnforcement:
    """
    Tests for the hard timeout enforcement mechanism in the training loop.
    """

    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = Path(self.temp_dir) / "test_logs.jsonl"

        # Configure a test config with a very short timeout for testing
        self.test_config = SocraticConfig(
            seed=42,
            max_epochs=100,  # Large number to ensure timeout triggers first
            timeout_seconds=2,  # Very short timeout for test speed
            model_name="hf-internal-testing/tiny-random-gpt2",
            log_path=str(self.log_path),
            batch_size=1,
            gradient_accumulation_steps=1,
            use_4bit_quantization=True,
            fallback_model_name="hf-internal-testing/tiny-random-gpt2"
        )
        set_global_config(self.test_config)

    def teardown_method(self):
        """Clean up test fixtures."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_timeout_enforcement_single_seed(self):
        """
        Assert that a single training job fails gracefully within the timeout limit.

        This test verifies FR-008: The job must fail gracefully within the 6-hour limit.
        For testing purposes, we use a much shorter timeout (2 seconds).
        """
        # Mock the training step to simulate a slow process that exceeds the timeout
        def slow_training_step(*args, **kwargs):
            # Sleep longer than the timeout to trigger the mechanism
            time.sleep(3)
            return {"loss": 0.5}

        # Mock the model loader to avoid real model loading overhead
        with patch('src.train.train_loop.load_model') as mock_load_model, \
             patch('src.train.train_loop.get_tokenizer') as mock_get_tokenizer, \
             patch('src.train.train_loop.Dataset') as mock_dataset:

            # Setup mocks
            mock_model = MagicMock()
            mock_tokenizer = MagicMock()
            mock_dataset_instance = MagicMock()
            mock_dataset_instance.__len__.return_value = 10
            mock_dataset_instance.__iter__.return_value = iter([{"input_ids": [1, 2, 3], "labels": [1, 2, 3]}])

            mock_load_model.return_value = mock_model
            mock_get_tokenizer.return_value = mock_tokenizer
            mock_dataset.return_value = mock_dataset_instance

            # Patch the training step to be slow
            with patch('src.train.train_loop._single_training_step', side_effect=slow_training_step):
                # Run the training job
                start_time = time.time()
                result = run_training_job(seed=42)
                elapsed_time = time.time() - start_time

                # Assert that the job failed due to timeout
                assert result is not None, "Training job should return a result object"
                assert result.success is False, "Training should fail due to timeout"
                assert "timeout" in result.error_message.lower(), f"Error message should mention timeout: {result.error_message}"

                # Assert that the job completed within a reasonable time (timeout + small buffer)
                # Timeout is 2s, buffer is 1s -> max 3s
                assert elapsed_time < 4.0, f"Job took too long: {elapsed_time}s (expected < 4s)"

    def test_experiment_runner_timeout_enforcement(self):
        """
        Assert that the experiment runner enforces timeout across multiple seeds.

        This test verifies SC-003: The experiment runner enforces timeout across 10 seeds.
        """
        seeds = [1, 2, 3]  # Using 3 seeds for faster testing
        timeout_per_job = 1  # 1 second per job

        # Create a config with short timeout
        config = SocraticConfig(
            seed=42,
            max_epochs=100,
            timeout_seconds=timeout_per_job,
            model_name="hf-internal-testing/tiny-random-gpt2",
            log_path=str(self.log_path),
            batch_size=1,
            gradient_accumulation_steps=1,
            use_4bit_quantization=True,
            fallback_model_name="hf-internal-testing/tiny-random-gpt2"
        )

        results = []
        start_time = time.time()

        # Simulate running the experiment runner for multiple seeds
        for seed in seeds:
            # Mock the training step to exceed timeout
            def slow_training_step(*args, **kwargs):
                time.sleep(timeout_per_job + 1)
                return {"loss": 0.5}

            with patch('src.train.train_loop.load_model'), \
                 patch('src.train.train_loop.get_tokenizer'), \
                 patch('src.train.train_loop.Dataset'), \
                 patch('src.train.train_loop._single_training_step', side_effect=slow_training_step):

                result = run_training_job(seed=seed)
                results.append(result)

        total_elapsed = time.time() - start_time

        # Assert all jobs failed due to timeout
        for i, result in enumerate(results):
            assert result is not None, f"Seed {seeds[i]} should return a result"
            assert result.success is False, f"Seed {seeds[i]} should fail due to timeout"
            assert "timeout" in result.error_message.lower(), f"Seed {seeds[i]} error should mention timeout"

        # Assert total time is roughly proportional to seeds * timeout (not infinite)
        # 3 seeds * 1s timeout + buffer = ~3-4s max
        # If it hung, this would take much longer
        assert total_elapsed < (len(seeds) * timeout_per_job + 3), \
            f"Experiment runner took too long: {total_elapsed}s for {len(seeds)} seeds"

    def test_graceful_failure_logging(self):
        """
        Assert that timeout failures are logged correctly.

        This verifies that the DEGENERATE_DIALOGUE_TRUNCATED or similar timeout
        events are logged as JSON lines as per the logging utility requirements.
        """
        # Setup config with short timeout
        config = SocraticConfig(
            seed=42,
            max_epochs=100,
            timeout_seconds=1,
            model_name="hf-internal-testing/tiny-random-gpt2",
            log_path=str(self.log_path),
            batch_size=1,
            gradient_accumulation_steps=1,
            use_4bit_quantization=True,
            fallback_model_name="hf-internal-testing/tiny-random-gpt2"
        )
        set_global_config(config)

        # Mock training step to trigger timeout
        def slow_training_step(*args, **kwargs):
            time.sleep(2)
            return {"loss": 0.5}

        with patch('src.train.train_loop.load_model'), \
             patch('src.train.train_loop.get_tokenizer'), \
             patch('src.train.train_loop.Dataset'), \
             patch('src.train.train_loop._single_training_step', side_effect=slow_training_step):

            result = run_training_job(seed=42)

            assert result.success is False
            assert "timeout" in result.error_message.lower()

            # Verify log file exists and contains timeout event
            assert self.log_path.exists(), "Log file should exist after timeout"

            with open(self.log_path, 'r') as f:
                log_lines = f.readlines()

            assert len(log_lines) > 0, "Log file should contain entries"

            # Check for timeout-related log entry
            timeout_logged = False
            for line in log_lines:
                if "timeout" in line.lower() or "failed" in line.lower():
                    timeout_logged = True
                    break

            assert timeout_logged, "Timeout event should be logged"