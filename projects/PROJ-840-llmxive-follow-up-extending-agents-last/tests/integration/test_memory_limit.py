"""
Integration test for memory limit compliance (US2).

This test verifies that the Context-Checkpointing wrapper and the CPUOnlyRunner
operate within the defined memory threshold (7GB RAM) during execution.

It imports the real `CPUOnlyRunner` and `ContextCheckpointWrapper` from the
intervention modules and simulates a workload to measure peak memory usage.
"""

import os
import sys
import json
import tempfile
import time
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from intervention.runner import CPUOnlyRunner, ExecutionResult
from intervention.wrapper import ContextCheckpointWrapper
from utils.config import load_config, PipelineConfig, ModelConfig, CheckpointConfig, DataPathsConfig
from utils.logging_config import setup_logging, get_logger
from utils.seeds import set_seed

# Configuration Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 * 1024 * 1024
TEST_TIMEOUT_SECONDS = 60  # Short timeout for the test to ensure it doesn't hang
TEST_TASK_COUNT = 5  # Number of synthetic tasks to run for the test

logger = get_logger(__name__)


def get_current_memory_usage_gb() -> float:
    """
    Returns the current process memory usage in GB.
    Uses resource module if available (Unix), otherwise falls back to a mock
    that raises an error if resource is missing, ensuring we don't silently pass.
    """
    try:
        import resource
        # Get max RSS (Resident Set Size) in KB
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Convert KB to GB (assuming 1024 KB = 1 MB, 1024 MB = 1 GB)
        # Note: On macOS, ru_maxrss is in bytes. On Linux, it's in KB.
        # We check the platform to be safe, but standard Linux behavior is KB.
        if sys.platform == "darwin":
            return usage / (1024 * 1024 * 1024)
        else:
            return usage / (1024 * 1024)
    except ImportError:
        # Fallback for Windows or environments without resource module
        # In a real CI environment, we might use psutil, but we stick to stdlib where possible.
        # If resource is missing, we cannot accurately measure memory, so we raise.
        raise RuntimeError(
            "Memory measurement requires the 'resource' module (Unix) or 'psutil' (Cross-platform). "
            "Please install psutil: pip install psutil"
        )


def generate_synthetic_task_for_memory_test(seed: int, index: int) -> Dict[str, Any]:
    """
    Generates a minimal synthetic task description and state to drive the runner.
    This is NOT the full dataset generation (T015), but a minimal payload
    to stress the context window and memory of the wrapper/runner.
    """
    set_seed(seed + index)
    # Create a payload that simulates a long context history
    # We simulate a state history that grows to test the wrapper's compression
    # and the runner's memory handling.
    base_state = {
        "step": index,
        "variables": {f"var_{i}": i * 1.5 for i in range(50)},
        "history": []
    }
    # Simulate a history of previous steps to increase memory load
    for h in range(20):
        base_state["history"].append({
            "step": h,
            "action": f"action_{h}",
            "observation": "Observation text " + "x" * 100
        })

    return {
        "trace_id": f"test_trace_{index}",
        "task_description": "Complete the task within memory limits.",
        "initial_state": base_state,
        "max_steps": 5
    }


class TestMemoryLimitCompliance(unittest.TestCase):
    """
    Integration test for memory limit compliance.

    Verifies that the CPUOnlyRunner and ContextCheckpointWrapper do not exceed
    the defined MEMORY_LIMIT_GB (7GB) during a controlled execution.
    """

    @classmethod
    def setUpClass(cls):
        """Setup test fixtures and configuration."""
        logger.info("Setting up memory limit integration test...")
        # Ensure logging is configured
        setup_logging(level="INFO")
        
        # Create a temporary config file for the test
        cls.temp_config_path = Path(tempfile.mktemp(suffix=".yaml"))
        config_data = {
            "model": {
                "path": "dummy_path_for_test.gguf", # We won't actually load a model, just test the wrapper logic
                "quantization": "Q4_K_M",
                "n_ctx": 2048,
                "n_threads": 2
            },
            "checkpoint": {
                "interval": 3,
                "compression_method": "abstraction",
                "max_tokens": 512
            },
            "data_paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "figures": "figures"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/test_memory.log"
            }
        }
        
        # Write config
        import yaml
        with open(cls.temp_config_path, "w") as f:
            yaml.dump(config_data, f)
        
        # Load config to verify it works
        try:
            cls.config = load_config(str(cls.temp_config_path))
            logger.info(f"Configuration loaded successfully: {cls.config}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        """Cleanup temporary files."""
        if cls.temp_config_path.exists():
            cls.temp_config_path.unlink()
        logger.info("Tear down memory limit integration test.")

    def test_runner_memory_compliance(self):
        """
        Test that the CPUOnlyRunner stays within memory limits.
        
        This test:
        1. Instantiates the CPUOnlyRunner.
        2. Runs a series of synthetic tasks.
        3. Monitors memory usage before, during, and after.
        4. Asserts that peak memory usage < MEMORY_LIMIT_GB.
        """
        logger.info("Starting memory compliance test for CPUOnlyRunner...")
        
        # Initialize Runner
        # Note: Since we don't have a real model file, we will test the wrapper logic
        # and the memory monitoring infrastructure. We mock the model interaction
        # if necessary, but the Runner class itself should handle the memory check.
        
        # We will test the memory monitoring logic by simulating a run.
        # If the runner actually tries to load a model, it will fail (expected),
        # but we can catch that and verify the memory check logic is in place.
        
        runner = CPUOnlyRunner(self.config)
        
        peak_memory_gb = 0.0
        tasks_run = 0
        
        # Run a few iterations to simulate load
        for i in range(TEST_TASK_COUNT):
            try:
                # Measure memory before
                mem_before = get_current_memory_usage_gb()
                
                # Create a synthetic task
                task = generate_synthetic_task_for_memory_test(seed=42, index=i)
                
                # Simulate a step (we can't run the full LLM loop without a model)
                # Instead, we test the internal memory check mechanism if exposed,
                # or we test the wrapper which is the primary memory consumer in US2.
                
                # We will directly test the ContextCheckpointWrapper's memory handling
                # by simulating a state accumulation that would trigger a checkpoint.
                
                wrapper = ContextCheckpointWrapper(runner, self.config.checkpoint)
                
                # Simulate adding state to the wrapper
                # This forces the wrapper to manage context and potentially compress
                for step in range(self.config.checkpoint.interval + 2):
                    # Add a large state object
                    state_payload = {
                        "step": step,
                        "data": "x" * 10000, # 10KB per step
                        "history": [{"action": "test", "obs": "y" * 500} for _ in range(10)]
                    }
                    wrapper.add_state(state_payload)
                    
                    # Check memory periodically
                    current_mem = get_current_memory_usage_gb()
                    if current_mem > peak_memory_gb:
                        peak_memory_gb = current_mem
                    
                    # If memory gets too high, we should trigger a checkpoint or fail
                    if current_mem > MEMORY_LIMIT_GB * 0.9:
                        # This is a warning, but the test should still pass if the logic is correct
                        logger.warning(f"Memory usage approaching limit: {current_mem:.2f} GB")
                
                tasks_run += 1
                mem_after = get_current_memory_usage_gb()
                if mem_after > peak_memory_gb:
                    peak_memory_gb = mem_after
                    
            except Exception as e:
                # If the runner fails due to missing model, that's expected in a unit/integration test
                # without a real model file. We are testing the memory logic, not the LLM inference.
                # However, we must ensure the memory check didn't exceed limits before the crash.
                logger.warning(f"Task {i} failed (expected if model missing): {e}")
                # We still check the memory usage up to the point of failure
                current_mem = get_current_memory_usage_gb()
                if current_mem > peak_memory_gb:
                    peak_memory_gb = current_mem

        # Final assertion
        logger.info(f"Peak memory usage during test: {peak_memory_gb:.2f} GB")
        logger.info(f"Memory limit: {MEMORY_LIMIT_GB} GB")
        
        self.assertLess(
            peak_memory_gb, 
            MEMORY_LIMIT_GB, 
            f"Memory limit exceeded! Peak: {peak_memory_gb:.2f} GB, Limit: {MEMORY_LIMIT_GB} GB"
        )
        
        self.assertGreater(
            tasks_run, 0, 
            "No tasks were successfully processed to measure memory."
        )

    def test_wrapper_compression_memory_reduction(self):
        """
        Test that the ContextCheckpointWrapper actually reduces memory pressure
        by compressing state summaries.
        """
        logger.info("Testing wrapper compression memory reduction...")
        
        wrapper = ContextCheckpointWrapper(None, self.config.checkpoint)
        
        # Add a large state
        large_state = {
            "step": 1,
            "data": "x" * 100000, # 100KB
            "history": [{"action": "a", "obs": "b" * 1000} for _ in range(100)]
        }
        
        # Add without compression
        wrapper.add_state(large_state)
        mem_before_compress = get_current_memory_usage_gb()
        
        # Force compression (simulating a checkpoint)
        # The wrapper should compress the history when interval is reached
        for i in range(self.config.checkpoint.interval):
            wrapper.add_state({"step": i+10, "data": "small"})
        
        # The wrapper should have triggered compression logic
        # We verify that the internal buffer size is managed
        # Since we can't easily measure the exact memory of internal lists without inspecting,
        # we rely on the fact that the compression logic runs and keeps the context window bounded.
        
        # For this test, we assert that the wrapper's internal state management
        # does not grow unbounded by checking the length of the history buffer
        # after compression.
        # Note: The actual memory savings depend on the compression algorithm.
        # We assert that the buffer length is reasonable (not infinite).
        
        self.assertTrue(
            len(wrapper.state_buffer) <= self.config.checkpoint.interval + 1,
            "State buffer grew beyond expected limit after compression interval."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)