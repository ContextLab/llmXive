import pytest
import numpy as np
import os
import sys

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from pruning import prune_fr04

class TestPruningFR04:
    """
    Tests for the prune_fr04 heuristic implementing FR-004.
    Criteria: usage_count == 0 AND min(sim_to_others) > 0.70.
    """

    def setup_method(self):
        """Set up basic embeddings for deterministic testing."""
        # Orthogonal vectors
        self.v1 = np.array([1.0, 0.0, 0.0])
        self.v2 = np.array([0.0, 1.0, 0.0])
        # Vector very close to v1
        self.v1_near = np.array([0.99, 0.01, 0.0])
        # Vector close to both v1 and v2 (to test min_sim > 0.7)
        # A vector that is ~0.71 similar to both [1,0,0] and [0,1,0]
        # cos(theta) = 0.71 => theta approx 45 deg. [0.71, 0.71, 0]
        self.v_redundant = np.array([0.71, 0.71, 0.0])
        self.v_redundant /= np.linalg.norm(self.v_redundant)

    def test_pruning_removes_redundant_unused_skill(self):
        """
        Verify that a skill with usage=0 and min_sim > 0.7 to all others is removed.
        """
        # Library: v_redundant is similar to both v1 and v2
        # sim(v_redundant, v1) = 0.71
        # sim(v_redundant, v2) = 0.71
        # min_sim = 0.71 > 0.70
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s2", "embedding_vector": self.v2, "usage_count": 1},
            {"skill_id": "s_red", "embedding_vector": self.v_redundant, "usage_count": 0},
        ]
        tasks = [] # No ground truth for now
        
        pruned, false_count = prune_fr04(library, tasks)
        
        assert len(pruned) == 2
        assert "s_red" not in [s["skill_id"] for s in pruned]
        assert false_count == 0

    def test_pruning_preserves_unique_unused_skill(self):
        """
        Verify that a skill with usage=0 but min_sim < 0.7 is preserved.
        """
        # Library: s_unique is similar to s1 but not s2
        # sim(v1_near, v1) = 0.99
        # sim(v1_near, v2) = 0.01
        # min_sim = 0.01 < 0.70
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s2", "embedding_vector": self.v2, "usage_count": 1},
            {"skill_id": "s_unique", "embedding_vector": self.v1_near, "usage_count": 0},
        ]
        tasks = []
        
        pruned, _ = prune_fr04(library, tasks)
        
        assert len(pruned) == 3
        assert "s_unique" in [s["skill_id"] for s in pruned]

    def test_pruning_preserves_used_skill(self):
        """
        Verify that a skill with usage > 0 is preserved regardless of similarity.
        """
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s_red", "embedding_vector": self.v_redundant, "usage_count": 1},
        ]
        tasks = []
        
        pruned, _ = prune_fr04(library, tasks)
        
        assert len(pruned) == 2

    def test_false_prune_count(self):
        """
        Verify that false_prune_count increments when a pruned skill is in ground truth.
        """
        library = [
            {"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 1},
            {"skill_id": "s2", "embedding_vector": self.v2, "usage_count": 1},
            {"skill_id": "s_red", "embedding_vector": self.v_redundant, "usage_count": 0},
        ]
        # s_red is required by a task
        tasks = [
            {"task_id": "t1", "ground_truth_path": ["s_red"]}
        ]
        
        pruned, false_count = prune_fr04(library, tasks)
        
        assert len(pruned) == 2
        assert false_count == 1

    def test_empty_or_small_library(self):
        """
        Verify the function handles small libraries without crashing.
        """
        library = [{"skill_id": "s1", "embedding_vector": self.v1, "usage_count": 0}]
        tasks = []
        pruned, false_count = prune_fr04(library, tasks)
        assert len(pruned) == 1
        assert false_count == 0

        pruned, false_count = prune_fr04([], tasks)
        assert len(pruned) == 0
        assert false_count == 0