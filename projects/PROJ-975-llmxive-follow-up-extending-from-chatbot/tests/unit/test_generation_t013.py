"""
Unit tests for T013: Ground-truth path assignment using distinct seed.
"""
import json
import os
import sys
import pytest
import random
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.generate_data import generate_tasks_with_ground_truth, NUM_TASKS

class TestGroundTruthAssignment:
    
    def test_seed_independence(self, tmp_path):
        """
        Verify that using different seeds produces different ground-truth assignments.
        """
        # Mock skill IDs
        skill_ids = [f"skill_{i:03d}" for i in range(100)]
        
        # Generate with Seed B = 42
        tasks_seed_42 = generate_tasks_with_ground_truth(42, skill_ids, num_tasks=10)
        
        # Generate with Seed B = 123
        tasks_seed_123 = generate_tasks_with_ground_truth(123, skill_ids, num_tasks=10)
        
        # Compare paths
        paths_42 = [t['ground_truth_path'] for t in tasks_seed_42]
        paths_123 = [t['ground_truth_path'] for t in tasks_seed_123]
        
        # They should be different (probability of collision is negligible)
        assert paths_42 != paths_123, "Ground truth paths should differ when using different seeds."
    
    def test_path_length_constraints(self):
        """
        Verify that all ground-truth paths have length between 3 and 5.
        """
        skill_ids = [f"skill_{i:03d}" for i in range(100)]
        tasks = generate_tasks_with_ground_truth(999, skill_ids, num_tasks=50)
        
        for t in tasks:
            length = t['path_length']
            assert 3 <= length <= 5, f"Task {t['id']} has invalid path length: {length}"
            assert len(t['ground_truth_path']) == length, "Path length mismatch with stored count."
    
    def test_unique_skills_in_path(self):
        """
        Verify that a single task's ground-truth path does not contain duplicate skill IDs.
        """
        skill_ids = [f"skill_{i:03d}" for i in range(100)]
        tasks = generate_tasks_with_ground_truth(42, skill_ids, num_tasks=50)
        
        for t in tasks:
            path = t['ground_truth_path']
            assert len(path) == len(set(path)), f"Task {t['id']} contains duplicate skills in path."
    
    def test_skill_ids_exist(self):
        """
        Verify that all skill IDs in ground-truth paths exist in the provided skill list.
        """
        skill_ids = [f"skill_{i:03d}" for i in range(100)]
        tasks = generate_tasks_with_ground_truth(42, skill_ids, num_tasks=50)
        
        for t in tasks:
            for skill_id in t['ground_truth_path']:
                assert skill_id in skill_ids, f"Task {t['id']} references non-existent skill {skill_id}"
    
    def test_determinism(self):
        """
        Verify that running the generation twice with the same seed produces identical results.
        """
        skill_ids = [f"skill_{i:03d}" for i in range(100)]
        seed = 42
        
        tasks_run_1 = generate_tasks_with_ground_truth(seed, skill_ids, num_tasks=20)
        tasks_run_2 = generate_tasks_with_ground_truth(seed, skill_ids, num_tasks=20)
        
        for t1, t2 in zip(tasks_run_1, tasks_run_2):
            assert t1['id'] == t2['id']
            assert t1['ground_truth_path'] == t2['ground_truth_path']
            assert t1['path_length'] == t2['path_length']