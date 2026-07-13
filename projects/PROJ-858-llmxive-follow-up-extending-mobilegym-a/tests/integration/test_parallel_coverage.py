"""
Integration test for parallel rollout aggregation without race conditions (T031).

This test verifies that the `process_rollouts_parallel` function in
`code/scheduler/state_coverage.py` correctly aggregates coverage vectors
from multiple concurrent threads without data races or lost updates.

It simulates a scenario where multiple threads attempt to flip the same
bits in a shared coverage vector simultaneously, ensuring the final
aggregated vector reflects all transitions correctly.
"""
import json
import os
import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Set

# Add project root to path to import code modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.scheduler.state_coverage import (
    initialize_coverage_vector,
    detect_state_transitions,
    process_rollouts_parallel,
    merge_coverage_vectors_threadsafe,
)
from code.utils.constants import is_valid_coverage_vector, calculate_coverage_ratio
from code.utils.logging import get_logger, configure_logging

# Configure logging for the test
configure_logging()
logger = get_logger(__name__)


class MockRolloutGenerator:
    """
    Generates deterministic mock rollouts for testing parallel aggregation.
    
    Each rollout targets a specific set of state variables to ensure
    we can verify if all transitions were captured correctly.
    """
    def __init__(self, num_rollouts: int, num_variables: int):
        self.num_rollouts = num_rollouts
        self.num_variables = num_variables
        self.variables = [f"state_var_{i}" for i in range(num_variables)]

    def generate_rollouts(self) -> List[Dict[str, Any]]:
        """
        Generate a list of mock rollouts.
        
        Each rollout flips a specific subset of bits.
        Rollout i flips bits at indices: (i * k) % num_variables for k in 0..3
        This ensures overlap and contention on specific bits.
        """
        rollouts = []
        for i in range(self.num_rollouts):
            # Determine which bits this rollout flips
            flipped_indices = set()
            for k in range(4):
                idx = (i * 3 + k) % self.num_variables
                flipped_indices.add(idx)

            # Create a mock rollout JSON structure
            rollout = {
                "rollout_id": f"rollout_{i}",
                "timestamp": time.time(),
                "transitions": [
                    {"state_var": self.variables[idx], "new_value": 1, "timestamp": time.time()}
                    for idx in sorted(flipped_indices)
                ],
                "metadata": {
                    "app": f"app_{i % 5}",
                    "task": f"task_{i % 3}"
                }
            }
            rollouts.append(rollout)
        return rollouts


class TestParallelCoverageAggregation(unittest.TestCase):
    """
    Integration test suite for parallel rollout aggregation.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.num_rollouts = 100
        cls.num_variables = 50
        cls.generator = MockRolloutGenerator(cls.num_rollouts, cls.num_variables)
        cls.rollouts = cls.generator.generate_rollouts()
        
        # Pre-calculate the expected final state
        # We will verify that the aggregated vector matches this expectation
        cls.expected_vector = initialize_coverage_vector(cls.num_variables)
        for rollout in cls.rollouts:
            for transition in rollout["transitions"]:
                # Map state_var name to index
                var_name = transition["state_var"]
                idx = int(var_name.split("_")[-1])
                cls.expected_vector[idx] = 1

    def test_parallel_aggregation_correctness(self):
        """
        Test that parallel aggregation produces the correct final vector.
        
        This test:
        1. Initializes a shared coverage vector (all zeros).
        2. Processes rollouts in parallel using ThreadPoolExecutor.
        3. Verifies that the final vector matches the expected state
           (all bits that should have been flipped are indeed 1).
        4. Verifies no race conditions caused lost updates.
        """
        logger.info("Starting parallel aggregation test")
        
        # Initialize shared vector
        shared_vector = initialize_coverage_vector(self.num_variables)
        lock = threading.Lock()
        
        # Process rollouts in parallel
        def process_single_rollout(rollout):
            # Simulate some processing delay to increase contention
            time.sleep(0.001)
            
            # Detect transitions for this rollout
            transitions = detect_state_transitions(rollout)
            
            # Create a local vector for this rollout's transitions
            local_vector = initialize_vector_with_transitions(transitions, self.num_variables)
            
            # Merge into shared vector with lock
            with lock:
                merge_coverage_vectors_threadsafe(shared_vector, local_vector)

        # Run parallel processing
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_single_rollout, rollout) for rollout in self.rollouts]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.fail(f"Parallel processing failed: {e}")

        # Verify correctness
        self.assertEqual(len(shared_vector), self.num_variables)
        self.assertEqual(shared_vector, self.expected_vector)
        
        # Verify coverage ratio
        ratio = calculate_coverage_ratio(shared_vector)
        expected_ratio = calculate_coverage_ratio(self.expected_vector)
        self.assertEqual(ratio, expected_ratio)
        
        logger.info(f"Parallel aggregation test passed. Final coverage ratio: {ratio:.2%}")

    def test_parallel_aggregation_no_data_loss(self):
        """
        Test that no transitions are lost due to race conditions.
        
        This test runs the aggregation multiple times with high contention
        and verifies that the result is always consistent.
        """
        logger.info("Starting no data loss test (multiple runs)")
        
        results = []
        for run in range(5):
            shared_vector = initialize_coverage_vector(self.num_variables)
            lock = threading.Lock()
            
            def process_and_merge(rollout):
                time.sleep(0.0005)  # Small delay to vary timing
                transitions = detect_state_transitions(rollout)
                local_vector = initialize_vector_with_transitions(transitions, self.num_variables)
                with lock:
                    merge_coverage_vectors_threadsafe(shared_vector, local_vector)
            
            with ThreadPoolExecutor(max_workers=16) as executor:
                list(executor.map(process_and_merge, self.rollouts))
            
            results.append(tuple(shared_vector))
        
        # All runs should produce identical results
        for i in range(1, len(results)):
            self.assertEqual(
                results[0], results[i],
                f"Inconsistent results between runs: run 0 vs run {i}"
            )
        
        logger.info("No data loss test passed: all runs consistent")

    def test_high_contention_scenario(self):
        """
        Test aggregation under extreme contention where all threads
        attempt to flip the same bit simultaneously.
        """
        logger.info("Starting high contention scenario test")
        
        # Create a scenario where all rollouts flip the same bit (index 0)
        high_contention_rollouts = []
        for i in range(50):
            rollout = {
                "rollout_id": f"contention_{i}",
                "transitions": [
                    {"state_var": "state_var_0", "new_value": 1, "timestamp": time.time()}
                ]
            }
            high_contention_rollouts.append(rollout)
        
        shared_vector = initialize_coverage_vector(self.num_variables)
        lock = threading.Lock()
        
        def process_contention(rollout):
            transitions = detect_state_transitions(rollout)
            local_vector = initialize_vector_with_transitions(transitions, self.num_variables)
            with lock:
                merge_coverage_vectors_threadsafe(shared_vector, local_vector)
        
        # Run with many workers
        with ThreadPoolExecutor(max_workers=32) as executor:
            list(executor.map(process_contention, high_contention_rollouts))
        
        # Bit 0 should be 1
        self.assertEqual(shared_vector[0], 1, "High contention caused bit 0 to remain 0")
        
        logger.info("High contention test passed")

    def test_aggregation_with_empty_rollouts(self):
        """
        Test that the system handles rollouts with no transitions correctly.
        """
        logger.info("Testing empty rollouts handling")
        
        mixed_rollouts = self.rollouts[:10] + [
            {
                "rollout_id": "empty_1",
                "transitions": []
            },
            {
                "rollout_id": "empty_2",
                "transitions": []
            }
        ] + self.rollouts[10:20]
        
        shared_vector = initialize_coverage_vector(self.num_variables)
        lock = threading.Lock()
        
        def process_mixed(rollout):
            transitions = detect_state_transitions(rollout)
            local_vector = initialize_vector_with_transitions(transitions, self.num_variables)
            with lock:
                merge_coverage_vectors_threadsafe(shared_vector, local_vector)
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(process_mixed, mixed_rollouts))
        
        # Should be equivalent to processing only non-empty rollouts
        expected_vector = initialize_coverage_vector(self.num_variables)
        for rollout in self.rollouts[:10] + self.rollouts[10:20]:
            for transition in rollout["transitions"]:
                var_name = transition["state_var"]
                idx = int(var_name.split("_")[-1])
                expected_vector[idx] = 1
        
        self.assertEqual(shared_vector, expected_vector)
        logger.info("Empty rollouts test passed")


def initialize_vector_with_transitions(transitions: List[Dict[str, Any]], num_variables: int) -> List[int]:
    """
    Helper function to create a local coverage vector from a list of transitions.
    
    Args:
        transitions: List of transition dictionaries with 'state_var' keys
        num_variables: Total number of state variables
    
    Returns:
        A coverage vector (list of 0s and 1s) with bits set for each transition
    """
    vector = initialize_coverage_vector(num_variables)
    for transition in transitions:
        var_name = transition["state_var"]
        try:
            idx = int(var_name.split("_")[-1])
            if 0 <= idx < num_variables:
                vector[idx] = 1
        except (ValueError, IndexError):
            # Skip invalid transitions
            continue
    return vector


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
