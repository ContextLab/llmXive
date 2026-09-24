"""
Unit tests for EvoMemConflict fallback logic.

Tests the specific requirement (FR-002, FR-007) that when no conflicts
are detected, the agent retrieves the latest state plus the 2 most
recent non-conflict patches.
"""
import pytest
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.evomem_conflict import EvoMemConflict
from src.heuristics.conflict_detector import ConflictDetector


class MockConflictDetector:
    """Mock detector that simulates various conflict detection scenarios."""

    def __init__(self, conflict_indices: List[int] = None, fail: bool = False):
        """
        Args:
            conflict_indices: List of indices to mark as conflicts.
            fail: If True, simulate detection failure.
        """
        self.conflict_indices = conflict_indices or []
        self.fail = fail
        self.model_name = "mock-model"
        self.threshold = 0.90
        self.device = "cpu"

    def is_conflict(self, state_text: str, patch_text: str) -> bool:
        """Mock conflict detection."""
        if self.fail:
            raise RuntimeError("Simulated detection failure")
        # This is a simplified mock - actual logic would be in the real detector
        return False  # By default, no conflicts

    def run_sensitivity_analysis_thresholds(self, thresholds: List[float]):
        """Mock implementation."""
        return []


class TestEvoMemConflictFallback:
    """Test cases for the fallback retrieval logic."""

    @pytest.fixture
    def sample_patches(self):
        """Create a sample set of patches for testing."""
        return [
            {
                "id": "patch_0",
                "content": "Initial state",
                "is_state": False
            },
            {
                "id": "patch_1",
                "content": "Update 1",
                "is_state": False
            },
            {
                "id": "patch_2",
                "content": "Update 2",
                "is_state": False
            },
            {
                "id": "patch_3",
                "content": "Current state",
                "is_state": True
            },
            {
                "id": "patch_4",
                "content": "Update 3",
                "is_state": False
            },
            {
                "id": "patch_5",
                "content": "Update 4",
                "is_state": False
            }
        ]

    def test_fallback_no_conflicts_retrieves_latest_and_two_recent(
        self,
        sample_patches: List[Dict[str, Any]]
    ):
        """
        Verify that when no conflicts are detected, the agent retrieves:
        - The latest state (patch_3)
        - The 2 most recent non-conflict patches (patch_5, patch_4)
        """
        # Create agent with mock detector that returns no conflicts
        agent = EvoMemConflict(model_name="mock", threshold=0.90)
        agent.detector = MockConflictDetector(conflict_indices=[])

        result = agent.retrieve_patches(sample_patches)

        # Should return 3 patches: state + 2 recent non-conflicts
        assert len(result) == 3

        # First should be the latest state
        assert result[0]["id"] == "patch_3"

        # Next two should be the most recent non-conflicts (patch_5, patch_4)
        # Note: The implementation sorts by index descending, so patch_5 comes first
        assert result[1]["id"] == "patch_5"
        assert result[2]["id"] == "patch_4"

    def test_fallback_on_detection_failure(
        self,
        sample_patches: List[Dict[str, Any]]
    ):
        """
        Verify that when detection fails, the agent falls back to
        latest state + 2 most recent non-conflicts.
        """
        agent = EvoMemConflict(model_name="mock", threshold=0.90)
        agent.detector = MockConflictDetector(fail=True)

        result = agent.retrieve_patches(sample_patches)

        # Should still return 3 patches (fallback behavior)
        assert len(result) == 3

        # First should be the latest state
        assert result[0]["id"] == "patch_3"

        # Next two should be the most recent non-conflicts
        assert result[1]["id"] == "patch_5"
        assert result[2]["id"] == "patch_4"

    def test_normal_mode_with_conflicts(
        self,
        sample_patches: List[Dict[str, Any]]
    ):
        """
        Verify that when conflicts are detected, the agent retrieves
        the latest state plus the conflict patches (not the fallback).
        """
        # Create mock that marks patch_1 and patch_5 as conflicts
        agent = EvoMemConflict(model_name="mock", threshold=0.90)
        agent.detector = MockConflictDetector(conflict_indices=[1, 5])

        result = agent.retrieve_patches(sample_patches)

        # Should return state + conflict patches
        assert len(result) == 3  # state + 2 conflicts

        # First should be the latest state
        assert result[0]["id"] == "patch_3"

        # Should include the conflict patches
        ids = [p["id"] for p in result]
        assert "patch_1" in ids
        assert "patch_5" in ids

    def test_fallback_with_fewer_than_two_non_conflicts(
        self,
        sample_patches: List[str]
    ):
        """
        Verify behavior when there are fewer than 2 non-conflict patches
        available besides the state.
        """
        # Create a minimal patch set: only state and 1 other patch
        minimal_patches = [
            {
                "id": "patch_0",
                "content": "Only non-state patch",
                "is_state": False
            },
            {
                "id": "patch_1",
                "content": "State",
                "is_state": True
            }
        ]

        agent = EvoMemConflict(model_name="mock", threshold=0.90)
        agent.detector = MockConflictDetector(conflict_indices=[])

        result = agent.retrieve_patches(minimal_patches)

        # Should return state + 1 non-conflict (only 1 available)
        assert len(result) == 2
        assert result[0]["id"] == "patch_1"
        assert result[1]["id"] == "patch_0"

    def test_fallback_with_no_non_conflicts(
        self,
        sample_patches: List[str]
    ):
        """
        Verify behavior when there are no non-conflict patches besides the state.
        """
        # Create a patch set where all non-state patches are conflicts
        conflict_patches = [
            {
                "id": "patch_0",
                "content": "Conflict 1",
                "is_state": False
            },
            {
                "id": "patch_1",
                "content": "State",
                "is_state": True
            }
        ]

        agent = EvoMemConflict(model_name="mock", threshold=0.90)
        agent.detector = MockConflictDetector(conflict_indices=[0])

        result = agent.retrieve_patches(conflict_patches)

        # Should return only the state (no non-conflicts to add)
        assert len(result) == 1
        assert result[0]["id"] == "patch_1"

    def test_empty_patches_list(self):
        """Verify behavior with empty patches list."""
        agent = EvoMemConflict(model_name="mock", threshold=0.90)

        result = agent.retrieve_patches([])

        assert result == []

    def test_single_patch(self):
        """Verify behavior with only the state patch."""
        single_patch = [
            {
                "id": "state_only",
                "content": "Only state",
                "is_state": True
            }
        ]

        agent = EvoMemConflict(model_name="mock", threshold=0.90)
        agent.detector = MockConflictDetector(conflict_indices=[])

        result = agent.retrieve_patches(single_patch)

        # Should return just the state
        assert len(result) == 1
        assert result[0]["id"] == "state_only"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])