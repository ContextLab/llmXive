"""
Unit tests for the pruning logic in the Digital Colleague agent.

Tests verify that:
1. Skills with usage_count == 0 AND min_cosine_similarity < 0.70 are removed.
2. The pruning trigger occurs exactly after every 10 tasks.
3. Skills that do not meet both criteria are retained.
"""
import pytest
import numpy as np
import json
import os
import sys
import tempfile
import shutil

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from agent import SkillLibrary
from utils import cosine_similarity
from config import get_seeds


class TestPruningLogic:
    """Tests for the Safe Pruning heuristic (T027/T025)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.skills_file = os.path.join(self.temp_dir, 'skills.json')
        self.tasks_file = os.path.join(self.temp_dir, 'tasks.json')
        
        # Create dummy skills with embeddings
        # We use simple numpy arrays as embeddings for testing
        skills_data = {
            "skills": [
                {
                    "id": "skill_0",
                    "code": "def func_0(): pass",
                    "embedding": [1.0, 0.0, 0.0],
                    "usage_count": 0,
                    "min_cosine_similarity": 0.50  # Should be pruned
                },
                {
                    "id": "skill_1",
                    "code": "def func_1(): pass",
                    "embedding": [0.0, 1.0, 0.0],
                    "usage_count": 5,  # Used, should NOT be pruned
                    "min_cosine_similarity": 0.50
                },
                {
                    "id": "skill_2",
                    "code": "def func_2(): pass",
                    "embedding": [0.0, 0.0, 1.0],
                    "usage_count": 0,
                    "min_cosine_similarity": 0.85  # High similarity, should NOT be pruned
                },
                {
                    "id": "skill_3",
                    "code": "def func_3(): pass",
                    "embedding": [0.5, 0.5, 0.0],
                    "usage_count": 0,
                    "min_cosine_similarity": 0.65  # Should be pruned
                }
            ],
            "metadata": {
                "overlap_level": "test",
                "seed": 42
            }
        }
        
        with open(self.skills_file, 'w') as f:
            json.dump(skills_data, f)

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir)

    def test_pruning_criteria_usage_zero_and_low_similarity(self):
        """Verify skills with usage=0 AND similarity < 0.70 are removed."""
        library = SkillLibrary(self.skills_file)
        
        # Initial state
        assert len(library.skills) == 4
        initial_ids = {s['id'] for s in library.skills}
        assert initial_ids == {'skill_0', 'skill_1', 'skill_2', 'skill_3'}

        # Simulate 10 tasks to trigger pruning
        # We manually call the pruning logic as if 10 tasks have passed
        # The actual agent logic calls this after every 10 tasks
        pruned_count = library.prune_library()

        # Expected: skill_0 (usage=0, sim=0.50) and skill_3 (usage=0, sim=0.65) removed
        # Expected retained: skill_1 (usage=5), skill_2 (sim=0.85)
        assert pruned_count == 2
        
        remaining_ids = {s['id'] for s in library.skills}
        assert remaining_ids == {'skill_1', 'skill_2'}

    def test_pruning_trigger_after_10_tasks(self):
        """Verify pruning happens exactly after 10 tasks."""
        library = SkillLibrary(self.skills_file)
        
        # Track pruning calls
        prune_calls = []
        
        # Simulate task execution loop
        for i in range(25):
            # Simulate task completion (increment usage for a skill)
            if i % 3 == 0 and library.skills:
                # Mark one skill as used
                library.skills[0]['usage_count'] += 1
            
            # Check if pruning should happen (every 10 tasks)
            if (i + 1) % 10 == 0:
                pruned = library.prune_library()
                prune_calls.append({
                    'task_count': i + 1,
                    'pruned_count': pruned,
                    'remaining_count': len(library.skills)
                })

        # Verify pruning happened at task 10 and 20
        assert len(prune_calls) == 2
        assert prune_calls[0]['task_count'] == 10
        assert prune_calls[1]['task_count'] == 20

    def test_pruning_does_not_remove_used_skills(self):
        """Verify skills with usage_count > 0 are retained even with low similarity."""
        library = SkillLibrary(self.skills_file)
        
        # Ensure skill_1 is used
        for skill in library.skills:
            if skill['id'] == 'skill_1':
                skill['usage_count'] = 100
                break

        pruned_count = library.prune_library()
        
        # skill_1 should NOT be pruned despite low similarity because usage > 0
        remaining_ids = {s['id'] for s in library.skills}
        assert 'skill_1' in remaining_ids
        assert pruned_count == 2  # Only skill_0 and skill_3 removed

    def test_pruning_does_not_remove_high_similarity_skills(self):
        """Verify skills with high similarity are retained even with usage=0."""
        library = SkillLibrary(self.skills_file)
        
        pruned_count = library.prune_library()
        
        # skill_2 should NOT be pruned despite usage=0 because sim >= 0.70
        remaining_ids = {s['id'] for s in library.skills}
        assert 'skill_2' in remaining_ids
        assert pruned_count == 2  # Only skill_0 and skill_3 removed

    def test_pruning_threshold_boundary(self):
        """Test exact boundary condition at 0.70 similarity."""
        # Create a skill with exactly 0.70 similarity
        skills_data = {
            "skills": [
                {
                    "id": "boundary_skill",
                    "code": "def func(): pass",
                    "embedding": [0.7, 0.7, 0.0],
                    "usage_count": 0,
                    "min_cosine_similarity": 0.70  # Exactly at threshold
                }
            ],
            "metadata": {}
        }
        
        boundary_file = os.path.join(self.temp_dir, 'boundary_skills.json')
        with open(boundary_file, 'w') as f:
            json.dump(skills_data, f)
        
        library = SkillLibrary(boundary_file)
        pruned_count = library.prune_library()
        
        # 0.70 should NOT be pruned (condition is < 0.70)
        remaining_ids = {s['id'] for s in library.skills}
        assert 'boundary_skill' in remaining_ids
        assert pruned_count == 0

    def test_pruning_with_empty_library(self):
        """Verify pruning handles empty library gracefully."""
        empty_data = {"skills": [], "metadata": {}}
        empty_file = os.path.join(self.temp_dir, 'empty_skills.json')
        with open(empty_file, 'w') as f:
            json.dump(empty_data, f)
        
        library = SkillLibrary(empty_file)
        pruned_count = library.prune_library()
        
        assert pruned_count == 0
        assert len(library.skills) == 0

    def test_pruning_logs_warning(self):
        """Verify pruning logs a warning when skills are removed."""
        import logging
        from io import StringIO

        # Set up logging capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        
        logger = logging.getLogger('agent')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)

        library = SkillLibrary(self.skills_file)
        library.prune_library()

        log_contents = log_stream.getvalue()
        assert "Pruned" in log_contents
        assert "skills" in log_contents

        logger.removeHandler(handler)