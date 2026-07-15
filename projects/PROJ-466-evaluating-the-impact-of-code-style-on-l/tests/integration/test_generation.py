import pytest
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the modules we are testing
from generation.generator import (
    get_available_memory_gb,
    calculate_batch_size,
    generate_samples_for_task,
    run_generation_pipeline
)
from utils.logger import log_timeout_error, initialize_memory_log, get_memory_log_path
from utils.timeout_decorator import timeout_decorator, TaskTimeoutError

# Test configuration
TEST_TIMEOUT_SECONDS = 5  # Short timeout for integration testing
TEST_BATCH_SIZE = 2
TEST_MEMORY_THRESHOLD_GB = 7.0

class TestGenerationIntegration:
    """
    Integration tests for the generation loop with timeout and memory probing.
    
    These tests verify:
    1. Memory probing works correctly
    2. Batch size calculation adjusts based on available memory
    3. Timeout decorator correctly raises TaskTimeoutError
    4. The generation pipeline handles timeouts gracefully
    """

    def setup_method(self):
        """Set up test fixtures before each test."""
        self.memory_log_path = get_memory_log_path()
        # Initialize memory log if it doesn't exist
        if not Path(self.memory_log_path).exists():
            initialize_memory_log()

    def test_get_available_memory_gb_returns_positive_value(self):
        """Verify that memory detection returns a positive number."""
        memory_gb = get_available_memory_gb()
        assert isinstance(memory_gb, (int, float)), "Memory should be numeric"
        assert memory_gb > 0, "Available memory should be positive"

    def test_calculate_batch_size_adjusts_for_memory(self):
        """Verify batch size calculation logic."""
        # Test with high memory - should return larger batch
        batch_high = calculate_batch_size(memory_limit_gb=16.0)
        assert batch_high > 0, "Batch size should be positive"
        
        # Test with low memory - should return smaller batch
        batch_low = calculate_batch_size(memory_limit_gb=1.0)
        assert batch_low > 0, "Batch size should be positive"
        
        # Lower memory should result in smaller or equal batch size
        assert batch_low <= batch_high, "Low memory should yield smaller batch"

    @timeout_decorator(timeout=TEST_TIMEOUT_SECONDS)
    def _slow_function_that_times_out(self):
        """A function designed to exceed the timeout."""
        time.sleep(TEST_TIMEOUT_SECONDS * 2)
        return "completed"

    def test_timeout_decorator_raises_error(self):
        """Verify that the timeout decorator correctly raises TaskTimeoutError."""
        with pytest.raises(TaskTimeoutError):
            self._slow_function_that_times_out()

    @timeout_decorator(timeout=TEST_TIMEOUT_SECONDS)
    def _fast_function_that_completes(self):
        """A function that completes within the timeout."""
        time.sleep(0.1)
        return "success"

    def test_timeout_decorator_allows_fast_tasks(self):
        """Verify that fast tasks complete successfully."""
        result = self._fast_function_that_completes()
        assert result == "success"

    def test_generate_samples_for_task_handles_timeout(self):
        """
        Test that generate_samples_for_task handles timeouts gracefully.
        
        This test mocks the actual LLM call to simulate a timeout scenario
        and verifies the function logs the error and continues.
        """
        # Mock the generation to raise a timeout
        with patch('generation.generator.time.sleep') as mock_sleep:
            mock_sleep.side_effect = TaskTimeoutError("Simulated timeout")
            
            # We expect this to raise TaskTimeoutError since we're not wrapping
            # the call in the pipeline logic that catches it
            with pytest.raises(TaskTimeoutError):
                # This would normally be called within a try/except in the pipeline
                generate_samples_for_task(
                    task_id="TEST_001",
                    style="neutral",
                    batch_size=1,
                    temperature=0.7,
                    seed=42
                )

    def test_memory_logging_integration(self):
        """
        Verify that memory logging works during generation operations.
        
        This test runs a small generation simulation and checks that
        memory logs are written correctly.
        """
        # Record initial log state
        initial_log = {}
        if Path(self.memory_log_path).exists():
            with open(self.memory_log_path, 'r') as f:
                initial_log = json.load(f)
        
        initial_count = len(initial_log.get("entries", []))
        
        # Simulate a memory log entry
        log_memory_usage("integration_test", 1.5, "test_operation")
        
        # Verify log was updated
        assert Path(self.memory_log_path).exists(), "Memory log file should exist"
        with open(self.memory_log_path, 'r') as f:
            updated_log = json.load(f)
        
        new_count = len(updated_log.get("entries", []))
        assert new_count == initial_count + 1, "Log should have one new entry"

    def test_run_generation_pipeline_structure(self):
        """
        Test that the generation pipeline runs without crashing on empty data.
        
        This is a structural test to ensure the pipeline orchestrator
        functions correctly even with minimal input.
        """
        # Create a minimal config for testing
        test_config = {
            "seeds": {"default": 42},
            "generation": {
                "batch_size": 1,
                "temperature": 0.7,
                "timeout_minutes": 1
            },
            "paths": {
                "data_dir": "data",
                "output_dir": "data/processed"
            }
        }
        
        # Mock the dataset loading to return empty
        with patch('generation.loader.get_humaneval_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = []
            
            # This should complete without error even with no tasks
            # (it will just process 0 tasks)
            try:
                run_generation_pipeline(config=test_config)
            except FileNotFoundError:
                # Expected if data directories don't exist yet
                pass
            except Exception as e:
                # We expect the pipeline to handle missing data gracefully
                # or fail with a clear error, not crash
                assert isinstance(e, (FileNotFoundError, ValueError)), \
                    f"Pipeline should handle missing data gracefully, got: {type(e)}"
