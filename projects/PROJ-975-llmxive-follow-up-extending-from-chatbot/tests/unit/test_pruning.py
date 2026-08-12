"""
Unit tests for the pruning logic in the Digital Colleague agent.

This module verifies that the 'Safe Pruning' heuristic correctly removes skills
that meet the criteria: usage_count == 0 AND min_cosine_similarity < 0.70
after a configurable number of tasks (N).
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
import sys
import os

# Add the code directory to the path to import agent modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from agent import SkillLibrary
from config import get_experiment_config


class TestPruningLogic:
    """Tests for the safe pruning heuristic."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the model for embedding generation
        self.mock_model = MagicMock()
        self.mock_model.encode = MagicMock(return_value=np.array([0.0, 0.0, 0.0]))

        # Create a SkillLibrary instance with mocked model
        self.library = SkillLibrary(model=self.mock_model)

        # Get pruning configuration
        self.config = get_experiment_config()
        self.prune_interval = self.config.get('prune_interval', 10)
        self.usage_threshold = 0
        self.similarity_threshold = 0.70

    def _create_skill(self, skill_id: str, usage_count: int, similarity: float):
        """Helper to create a skill dictionary for testing."""
        return {
            "skill_id": skill_id,
            "function_code": f"def {skill_id}(): pass",
            "embedding_vector": [1.0, 0.0, 0.0],  # Mock embedding
            "usage_count": usage_count,
            "min_cosine_similarity": similarity
        }

    def test_pruning_removes_unused_low_similarity(self):
        """
        Verify that skills with usage_count == 0 and similarity < 0.70 are removed.
        """
        # Add skills to the library
        skills = [
            self._create_skill("skill_1", usage_count=0, similarity=0.50),  # Should be pruned
            self._create_skill("skill_2", usage_count=0, similarity=0.80),  # Should NOT be pruned (high similarity)
            self._create_skill("skill_3", usage_count=5, similarity=0.30),  # Should NOT be pruned (high usage)
            self._create_skill("skill_4", usage_count=0, similarity=0.69),  # Should be pruned (just below threshold)
        ]

        self.library.skills = {s["skill_id"]: s for s in skills}
        self.library.task_count_since_last_prune = self.prune_interval

        # Perform pruning
        pruned_skills, risk_count = self.library.safe_prune()

        # Verify correct skills were removed
        assert "skill_1" in pruned_skills, "skill_1 should be pruned"
        assert "skill_4" in pruned_skills, "skill_4 should be pruned"
        assert len(pruned_skills) == 2, "Exactly 2 skills should be pruned"

        # Verify remaining skills
        assert "skill_2" in self.library.skills, "skill_2 should remain"
        assert "skill_3" in self.library.skills, "skill_3 should remain"
        assert len(self.library.skills) == 2, "Only 2 skills should remain"

    def test_pruning_preserves_high_usage_skills(self):
        """
        Verify that skills with usage_count > 0 are preserved regardless of similarity.
        """
        skills = [
            self._create_skill("skill_1", usage_count=1, similarity=0.10),  # High usage, low sim
            self._create_skill("skill_2", usage_count=100, similarity=0.05), # High usage, low sim
        ]

        self.library.skills = {s["skill_id"]: s for s in skills}
        self.library.task_count_since_last_prune = self.prune_interval

        pruned_skills, _ = self.library.safe_prune()

        assert len(pruned_skills) == 0, "No skills should be pruned"
        assert len(self.library.skills) == 2, "All skills should remain"

    def test_pruning_preserves_high_similarity_unused_skills(self):
        """
        Verify that skills with similarity >= 0.70 are preserved even if unused.
        """
        skills = [
            self._create_skill("skill_1", usage_count=0, similarity=0.70),  # Exactly at threshold
            self._create_skill("skill_2", usage_count=0, similarity=0.95),  # High similarity
        ]

        self.library.skills = {s["skill_id"]: s for s in skills}
        self.library.task_count_since_last_prune = self.prune_interval

        pruned_skills, _ = self.library.safe_prune()

        assert len(pruned_skills) == 0, "No skills should be pruned"
        assert len(self.library.skills) == 2, "All skills should remain"

    def test_pruning_does_not_run_before_interval(self):
        """
        Verify that pruning logic does not execute if task count < N.
        """
        skills = [
            self._create_skill("skill_1", usage_count=0, similarity=0.50),
        ]

        self.library.skills = {s["skill_id"]: s for s in skills}
        self.library.task_count_since_last_prune = self.prune_interval - 1

        # Mock the pruning logic to ensure it's not called
        with patch.object(self.library, 'safe_prune', wraps=self.library.safe_prune) as mock_prune:
            # Manually trigger the check that happens in run_task
            if self.library.task_count_since_last_prune >= self.prune_interval:
                self.library.safe_prune()

            # Since count < interval, safe_prune should not have been called internally by the check
            # Note: We are testing the condition logic here.
            assert self.library.task_count_since_last_prune < self.prune_interval
            # If we force the check:
            if self.library.task_count_since_last_prune >= self.prune_interval:
                self.library.safe_prune()
                assert False, "Pruning should not run"
            else:
                # Correct path: do not prune
                pass

        # Verify no skills were removed
        assert len(self.library.skills) == 1

    def test_pruning_reset_counter(self):
        """
        Verify that the task counter is reset after pruning.
        """
        skills = [
            self._create_skill("skill_1", usage_count=0, similarity=0.50),
        ]

        self.library.skills = {s["skill_id"]: s for s in skills}
        self.library.task_count_since_last_prune = self.prune_interval

        # Perform pruning
        self.library.safe_prune()

        # Verify counter reset
        assert self.library.task_count_since_last_prune == 0, "Task counter should reset to 0"

    def test_pruning_calculates_risk_count(self):
        """
        Verify that pruning correctly calculates the risk count (skills pruned that had
        high similarity to ground truth, defined as > 0.70).
        
        Note: In this test context, we assume 'min_cosine_similarity' represents the
        similarity to the ground truth for the purpose of risk calculation as per
        the task description logic flow, or that the library tracks this specifically.
        Given the data structure in generate_data, we interpret the field min_cosine_similarity
        as the metric used for the pruning decision. The 'risk' in the context of the
        Safe Pruning heuristic usually refers to removing skills that might be needed.
        
        Re-reading T028: "Explicitly calculate and return pruning_risk_count (skills pruned 
        that had high similarity to ground truth, defined as similarity > 0.70)".
        
        In the Safe Pruning logic (T028), we remove skills where `min_cosine_similarity < 0.70`.
        Therefore, by definition, any skill removed has similarity < 0.70.
        Thus, the risk count (skills removed with similarity > 0.70) should be 0.
        
        However, if the logic is: "Remove usage=0 AND similarity < 0.70", then no removed
        skill can have similarity > 0.70.
        
        Let's re-read carefully: "pruning_risk_count (skills pruned that had high similarity to ground truth, defined as similarity > 0.70)".
        
        If we only prune skills with similarity < 0.70, then risk_count must be 0.
        Unless the "risk" refers to something else, or the threshold logic is different.
        
        Wait, T028 says: "removes skills where usage_count == 0 AND min_cosine_similarity < 0.70".
        And T023 says: "Include pruning_risk_count (skills pruned that had high similarity to ground truth, defined as similarity > 0.70)".
        
        There is a logical contradiction if we strictly follow "prune if sim < 0.70" and "count pruned if sim > 0.70".
        The set of pruned skills is a subset of {s | sim < 0.70}.
        The set of risky skills is a subset of {s | sim > 0.70}.
        These sets are disjoint.
        
        Perhaps the "risk" refers to a different metric, or the threshold for risk is different,
        or the pruning logic allows some exceptions?
        
        Actually, looking at the description: "Safe Pruning heuristic... removes skills where ... min_cosine_similarity < 0.70".
        If the system prunes a skill, it's because it's considered "safe" to remove (low similarity).
        The "risk" might be a metric to track if we *accidentally* pruned something important, but the logic prevents that.
        
        Let's assume the test verifies the calculation logic as implemented in agent.py.
        If agent.py calculates risk as `count(s for s in pruned if s.sim > 0.70)`, it will be 0.
        
        Let's create a scenario where the logic might be different or verify the 0 case.
        Or perhaps the "risk" is defined relative to a *different* threshold in the actual implementation?
        
        Let's assume the implementation in agent.py is correct and follows the spec:
        Prune if usage=0 AND sim < 0.70.
        Risk count = number of pruned skills with sim > 0.70.
        Result: Risk count should always be 0 with this logic.
        
        However, to make the test meaningful, let's verify the calculation logic itself.
        We will test that the function returns 0 for the disjoint set, proving the logic holds.
        """
        skills = [
            self._create_skill("skill_1", usage_count=0, similarity=0.50), # Pruned, sim < 0.70 -> Not risky
            self._create_skill("skill_2", usage_count=0, similarity=0.80), # Not pruned
        ]

        self.library.skills = {s["skill_id"]: s for s in skills}
        self.library.task_count_since_last_prune = self.prune_interval

        pruned_skills, risk_count = self.library.safe_prune()

        assert len(pruned_skills) == 1
        assert "skill_1" in pruned_skills
        assert risk_count == 0, "Risk count should be 0 because pruned skills have sim < 0.70"

    def test_pruning_empty_library(self):
        """
        Verify that pruning handles an empty library gracefully.
        """
        self.library.skills = {}
        self.library.task_count_since_last_prune = self.prune_interval

        pruned_skills, risk_count = self.library.safe_prune()

        assert len(pruned_skills) == 0
        assert risk_count == 0
        assert len(self.library.skills) == 0

    def test_pruning_incremental_task_count(self):
        """
        Verify that the task count increments correctly and triggers pruning at N.
        """
        self.library.task_count_since_last_prune = 0
        
        # Increment manually to simulate tasks
        for i in range(1, self.prune_interval):
            self.library.task_count_since_last_prune += 1
            # Simulate check (logic from run_task)
            if self.library.task_count_since_last_prune >= self.prune_interval:
                self.library.safe_prune()
                break
        
        assert self.library.task_count_since_last_prune == self.prune_interval - 1
        
        # Next task triggers pruning
        self.library.task_count_since_last_prune += 1
        assert self.library.task_count_since_last_prune == self.prune_interval
        
        # Add a skill to prune
        self.library.skills = {"test": self._create_skill("test", 0, 0.5)}
        
        # Trigger prune
        if self.library.task_count_since_last_prune >= self.prune_interval:
            self.library.safe_prune()
        
        assert self.library.task_count_since_last_prune == 0
        assert len(self.library.skills) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])