import pytest
from pathlib import Path
import sys
import os
from src.agents.evomem_conflict import EvoMemConflict
from typing import List, Dict, Any

# Mock the ConflictDetector to avoid loading real models in unit tests
class MockConflictDetector:
    def __init__(self):
        self.load_called = False

    def load_model(self):
        self.load_called = True

    def detect(self, patch_text: str, reference_text: str) -> float:
        # Simulate detection logic
        # If patch contains "CONFLICT", return high score
        if "CONFLICT" in patch_text:
            return 0.95
        return 0.50

# Patch the import in evomem_conflict
import src.agents.evomem_conflict as evomem_conflict_module
original_detector = evomem_conflict_module.ConflictDetector

def setup_module(module):
    evomem_conflict_module.ConflictDetector = MockConflictDetector

def teardown_module(module):
    evomem_conflict_module.ConflictDetector = original_detector


class TestEvoMemConflictInitialization:
    def test_init_default(self):
        agent = EvoMemConflict()
        assert agent.name == "EvoMem-Conflict"
        assert agent.fallback_non_conflict_count == 2

    def test_init_custom_seed(self):
        agent = EvoMemConflict(seed=123)
        assert agent.fallback_non_conflict_count == 2


class TestEvoMemConflictRetrieval:
    def test_no_conflicts_fallback(self):
        """
        Test that if no conflicts are detected, the agent retrieves
        the latest state plus the 2 most recent non-conflict patches.
        """
        agent = EvoMemConflict()
        
        # Create patches: 4 history + 1 latest
        # None contain "CONFLICT", so detector returns 0.5 (no conflict)
        patches = [
            {"patch": "Patch 1", "id": 1},
            {"patch": "Patch 2", "id": 2},
            {"patch": "Patch 3", "id": 3},
            {"patch": "Patch 4", "id": 4}, # Most recent non-conflict
            {"patch": "Latest State", "id": 5} # Latest
        ]
        
        context = agent.retrieve_context(patches)
        
        # Expect: Latest State + Patch 3 + Patch 4 (2 most recent non-conflicts)
        # Order: [Latest, Patch 4, Patch 3] or [Latest, Patch 3, Patch 4]?
        # Implementation: [latest_state] + recent_non_conflicts
        # recent_non_conflicts = non_conflicts[-2:] -> [Patch 3, Patch 4]
        # So result: [Latest, Patch 3, Patch 4]
        
        assert len(context) == 3
        assert context[0]["patch"] == "Latest State"
        # Check that the last two are the most recent non-conflicts
        assert context[1]["patch"] == "Patch 3"
        assert context[2]["patch"] == "Patch 4"

    def test_with_conflicts(self):
        """
        Test that if conflicts are detected, only latest + conflicts are returned.
        """
        agent = EvoMemConflict()
        
        patches = [
            {"patch": "Patch 1", "id": 1},
            {"patch": "CONFLICT Patch 2", "id": 2}, # Conflict
            {"patch": "Patch 3", "id": 3},
            {"patch": "CONFLICT Patch 4", "id": 4}, # Conflict
            {"patch": "Latest State", "id": 5}
        ]
        
        context = agent.retrieve_context(patches)
        
        # Expect: Latest State + Conflict 2 + Conflict 4
        assert len(context) == 3
        assert context[0]["patch"] == "Latest State"
        # The order of conflicts depends on detection order
        conflict_patches = [p for p in context[1:] if "CONFLICT" in p["patch"]]
        assert len(conflict_patches) == 2

    def test_empty_history(self):
        """
        Test behavior when only latest state exists.
        """
        agent = EvoMemConflict()
        patches = [{"patch": "Latest State", "id": 1}]
        
        context = agent.retrieve_context(patches)
        assert len(context) == 1
        assert context[0]["patch"] == "Latest State"

    def test_fallback_with_insufficient_non_conflicts(self):
        """
        Test fallback when fewer than 2 non-conflicts exist.
        """
        agent = EvoMemConflict()
        
        patches = [
            {"patch": "CONFLICT 1", "id": 1},
            {"patch": "Latest State", "id": 2}
        ]
        
        context = agent.retrieve_context(patches)
        # Only 0 non-conflicts in history.
        # Should return Latest + 0 non-conflicts?
        # Or does it fail?
        # Logic: recent_non_conflicts = non_conflicts[-2:] -> []
        # Result: [Latest]
        assert len(context) == 1
        assert context[0]["patch"] == "Latest State"


class TestEvoMemConflictExecution:
    def test_execute_returns_metrics(self):
        agent = EvoMemConflict()
        
        patches = [
            {"patch": "Patch 1", "id": 1},
            {"patch": "Latest State", "id": 2}
        ]
        
        result = agent.execute(patches, "Test Task")
        
        assert "output" in result
        assert "metrics" in result
        assert "context_tokens" in result["metrics"]
        assert "inference_time" in result["metrics"]
        assert "success_status" in result["metrics"]
        assert result["metrics"]["agent_variant"] == "EvoMem-Conflict"