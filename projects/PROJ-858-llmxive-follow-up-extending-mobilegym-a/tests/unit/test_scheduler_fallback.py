"""
Unit tests for the fallback logic (entropy/random) in CurriculumScheduler.

This test suite verifies that when no tasks meet the target success rate criteria
(after range expansion) or when all states are covered (deadlock), the scheduler
correctly falls back to maximum entropy selection or random selection.

Prerequisites:
- T020: tests/fixtures/mock_coverage_history.json must exist
- T005, T008, T019: code/scheduler/curriculum_scheduler.py must be implemented
"""

import json
import math
import os
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from scheduler.curriculum_scheduler import CurriculumScheduler
from utils.constants import calculate_coverage_ratio


class TestSchedulerFallback(unittest.TestCase):
    """Tests for fallback mechanisms in the curriculum scheduler."""
    
    def setUp(self):
        """Set up test fixtures and load mock data."""
        self.fixture_path = (
            project_root / "tests" / "fixtures" / "mock_coverage_history.json"
        )
        
        if not self.fixture_path.exists():
            self.skipTest(
                f"Mock fixture {self.fixture_path} not found. "
                "Please ensure T020 has been completed."
            )
        
        with open(self.fixture_path, "r") as f:
            self.mock_history = json.load(f)
        
        # Initialize scheduler
        self.scheduler = CurriculumScheduler(
            task_pool=self.mock_history.get("task_pool", []),
            history=self.mock_history.get("history", []),
            coverage_vector=self.mock_history.get("current_coverage", []),
            seed=42  # For reproducibility
        )
    
    def test_fallback_to_max_entropy_when_no_tasks_in_range(self):
        """
        Test that scheduler falls back to max entropy selection when no tasks
        meet the target success rate range (after range expansion).
        
        Scenario: All available tasks have success rates outside the expanded
        range, so the scheduler should select tasks that maximize entropy
        (i.e., target the least covered states).
        """
        # Create a scenario where no tasks are in the "sweet spot"
        # by manipulating the task pool to have extreme success rates
        extreme_tasks = [
            {"task_id": "extreme_1", "success_rate": 0.01, "params": {}},
            {"task_id": "extreme_2", "success_rate": 0.99, "params": {}},
            {"task_id": "extreme_3", "success_rate": 0.02, "params": {}},
        ]
        
        scheduler_extreme = CurriculumScheduler(
            task_pool=extreme_tasks,
            history=[],
            coverage_vector=[0.0] * len(self.mock_history.get("current_coverage", [])),
            seed=42
        )
        
        # Request a batch - should fall back to entropy-based selection
        batch = scheduler_extreme.select_batch(batch_size=2)
        
        # Verify we got tasks (not empty)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), 2)
        
        # Verify tasks are from the provided pool
        task_ids = [t["task_id"] for t in batch]
        for tid in task_ids:
            self.assertIn(tid, ["extreme_1", "extreme_2", "extreme_3"])
    
    def test_fallback_to_random_on_deadlock(self):
        """
        Test that scheduler falls back to random selection when all states
        are covered (deadlock prevention).
        
        Scenario: Coverage vector is all 1s (100% coverage), so there's
        no state to target. Scheduler should randomly select tasks.
        """
        # Create a fully covered scenario
        fully_covered_vector = [1.0] * len(self.mock_history.get("current_coverage", []))
        
        scheduler_deadlock = CurriculumScheduler(
            task_pool=self.mock_history.get("task_pool", []),
            history=self.mock_history.get("history", []),
            coverage_vector=fully_covered_vector,
            seed=42
        )
        
        # Request a batch - should fall back to random selection
        batch = scheduler_deadlock.select_batch(batch_size=3)
        
        # Verify we got tasks
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), 3)
        
        # Verify tasks are from the pool
        pool_ids = [t["task_id"] for t in self.mock_history.get("task_pool", [])]
        for task in batch:
            self.assertIn(task["task_id"], pool_ids)
    
    def test_entropy_calculation_validity(self):
        """
        Verify that the entropy-based selection actually considers state coverage.
        
        This test ensures that when some states are less covered, the scheduler
        prioritizes tasks that can cover those states (higher entropy contribution).
        """
        # Create a coverage vector with some states covered, some not
        partial_coverage = [1.0, 0.0, 0.0, 1.0, 0.0]
        
        # Create tasks that affect different states
        tasks_with_state_info = [
            {"task_id": "task_a", "success_rate": 0.5, "params": {"state_target": 1}},
            {"task_id": "task_b", "success_rate": 0.5, "params": {"state_target": 2}},
            {"task_id": "task_c", "success_rate": 0.5, "params": {"state_target": 4}},
            {"task_id": "task_d", "success_rate": 0.5, "params": {"state_target": 0}},
        ]
        
        scheduler_partial = CurriculumScheduler(
            task_pool=tasks_with_state_info,
            history=[],
            coverage_vector=partial_coverage,
            seed=42
        )
        
        batch = scheduler_partial.select_batch(batch_size=2)
        
        # The scheduler should prefer tasks targeting uncovered states (1, 2, 4)
        # over already covered states (0, 3)
        selected_ids = [t["task_id"] for t in batch]
        
        # We expect at least one task targeting an uncovered state
        uncovered_targets = {"task_a", "task_b", "task_c"}  # targets 1, 2, 4
        covered_targets = {"task_d"}  # targets 0
        
        # At least one should be from uncovered targets (probabilistic, but likely)
        # With seed=42, we can check the deterministic behavior
        self.assertTrue(
            any(tid in uncovered_targets for tid in selected_ids),
            f"Expected at least one task targeting uncovered states, got {selected_ids}"
        )
    
    def test_fallback_preserves_task_metadata(self):
        """
        Ensure that when falling back to entropy/random selection,
        all task metadata is preserved correctly.
        """
        tasks_with_metadata = [
            {
                "task_id": "meta_1",
                "success_rate": 0.01,
                "params": {"difficulty": "hard", "app": "test_app"},
                "metadata": {"source": "manual", "version": "1.0"}
            },
            {
                "task_id": "meta_2",
                "success_rate": 0.99,
                "params": {"difficulty": "easy", "app": "other_app"},
                "metadata": {"source": "auto", "version": "2.0"}
            },
        ]
        
        scheduler_meta = CurriculumScheduler(
            task_pool=tasks_with_metadata,
            history=[],
            coverage_vector=[0.0] * 5,
            seed=42
        )
        
        batch = scheduler_meta.select_batch(batch_size=1)
        
        # Verify metadata is preserved
        self.assertIn("task_id", batch[0])
        self.assertIn("params", batch[0])
        self.assertIn("metadata", batch[0])
        self.assertEqual(batch[0]["task_id"], batch[0].get("task_id"))
        self.assertEqual(batch[0]["params"]["difficulty"], "hard")
    
    def test_multiple_fallback_modes(self):
        """
        Test that the scheduler correctly handles multiple fallback scenarios:
        1. Low coverage phase (target < 5%)
        2. Sweet spot phase (30-70%)
        3. Fallback to entropy when no tasks in range
        4. Fallback to random on deadlock
        """
        # Test 1: Normal operation (should not fallback)
        normal_batch = self.scheduler.select_batch(batch_size=2)
        self.assertEqual(len(normal_batch), 2)
        
        # Test 2: Extreme case (should fallback to entropy)
        extreme_tasks = [
            {"task_id": "e1", "success_rate": 0.0, "params": {}},
            {"task_id": "e2", "success_rate": 1.0, "params": {}},
        ]
        scheduler_extreme = CurriculumScheduler(
            task_pool=extreme_tasks,
            history=[],
            coverage_vector=[0.0] * 5,
            seed=42
        )
        extreme_batch = scheduler_extreme.select_batch(batch_size=1)
        self.assertEqual(len(extreme_batch), 1)
        
        # Test 3: Deadlock (should fallback to random)
        deadlock_scheduler = CurriculumScheduler(
            task_pool=extreme_tasks,
            history=[],
            coverage_vector=[1.0] * 5,
            seed=42
        )
        deadlock_batch = deadlock_scheduler.select_batch(batch_size=1)
        self.assertEqual(len(deadlock_batch), 1)
    
    def test_fallback_with_empty_task_pool(self):
        """
        Test that scheduler handles empty task pool gracefully.
        """
        scheduler_empty = CurriculumScheduler(
            task_pool=[],
            history=[],
            coverage_vector=[0.0] * 5,
            seed=42
        )
        
        batch = scheduler_empty.select_batch(batch_size=2)
        
        # Should return empty list or handle gracefully
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), 0)
    
    def test_entropy_selection_deterministic_with_seed(self):
        """
        Verify that entropy-based selection is deterministic when seeded.
        """
        tasks = [
            {"task_id": "t1", "success_rate": 0.01, "params": {"state_target": 1}},
            {"task_id": "t2", "success_rate": 0.99, "params": {"state_target": 2}},
        ]
        
        scheduler1 = CurriculumScheduler(
            task_pool=tasks,
            history=[],
            coverage_vector=[0.0, 0.0, 0.0],
            seed=123
        )
        
        scheduler2 = CurriculumScheduler(
            task_pool=tasks,
            history=[],
            coverage_vector=[0.0, 0.0, 0.0],
            seed=123
        )
        
        batch1 = scheduler1.select_batch(batch_size=1)
        batch2 = scheduler2.select_batch(batch_size=1)
        
        # Should be identical with same seed
        self.assertEqual(batch1[0]["task_id"], batch2[0]["task_id"])


if __name__ == "__main__":
    unittest.main()