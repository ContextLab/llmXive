import pytest
import numpy as np
import os
import sys

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from pruning import prune_fr04

class TestPruningFR04:
    """
    Tests for the prune_fr04 heuristic implementing corrected FR-004.
    Criteria: usage_count == 0 AND max(sim_to_others) > 0.70.
    """

    def setup_method(self):
        """Set up basic embeddings for deterministic testing."""
        # Orthogonal vectors
        self.v1 = np.array([1.0, 0.0, 0.0])
        self.v2 = np.array([0.0, 1.0, 0.0])
        # Vector highly similar to v1 (sim ~ 0.99)
        self.v1_near = np.array([0.99, 0.01, 0.0])
        # Vector that is similar to v1 but not v2
        # sim(v_redundant, v1) = 0.8, sim(v_redundant, v2) = 0.2
        self.v_redundant = np.array([0.8, 0.6, 0.0])
        self.v_redundant /= np.linalg.norm(self.v_redundant)

    def test_pruning_removes_redundant_unused_skill(self):
        """
        Verify that a skill with usage=0 and max_sim > 0.7 to at least one other is removed.
        """
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s2", "embedding_vector": self.v2, "usage_count": 1},
            {"skill_id": "s_red", "embedding_vector": self.v_redundant, "usage_count": 0},
        ]
        pruned, false_count = prune_fr04(library)
        assert len(pruned) == 2
        assert "s_red" not in [s["skill_id"] for s in pruned]
        assert false_count == 0

    def test_pruning_preserves_unique_unused_skill(self):
        """
        Verify that a skill with usage=0 but max_sim < 0.7 to all others is preserved.
        """
        v_unique = np.array([0.0, 0.0, 1.0])
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s2", "embedding_vector": self.v2, "usage_count": 1},
            {"skill_id": "s_unique", "embedding_vector": v_unique, "usage_count": 0},
        ]
        pruned, false_count = prune_fr04(library)
        assert len(pruned) == 3
        assert "s_unique" in [s["skill_id"] for s in pruned]
        assert false_count == 0

    def test_pruning_preserves_used_skill(self):
        """
        Verify that a skill with usage > 0 is preserved regardless of similarity.
        """
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s_red", "embedding_vector": self.v_redundant, "usage_count": 1},
        ]
        pruned, false_count = prune_fr04(library)
        assert len(pruned) == 2
        assert false_count == 0

    def test_empty_or_small_library(self):
        """
        Verify the function handles small libraries without crashing.
        """
        library = [{"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 0}]
        pruned, false_count = prune_fr04(library)
        assert len(pruned) == 1
        assert false_count == 0

        pruned, false_count = prune_fr04([])
        assert len(pruned) == 0
        assert false_count == 0