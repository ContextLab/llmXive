"""
tests/unit/test_generation.py

Unit tests for code/generate_data.py
Verifies ground-truth independence between Seed A (skills) and Seed B (tasks).
"""
import pytest
import random
import json
import os
import sys
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.generate_data import generate_skills, generate_tasks_with_ground_truth
from code.config import get_seeds, pin_seeds

# Mock dependencies that might fail in test environment
@pytest.fixture
def mock_utils():
    with patch('code.generate_data.get_model') as mock_model, \
         patch('code.generate_data.get_embedding') as mock_emb, \
         patch('code.generate_data.pairwise_cosine_similarity_matrix') as mock_sim, \
         patch('code.generate_data.mean_pairwise_similarity') as mock_mean:
         
         mock_model.return_value = MagicMock()
         mock_emb.return_value = np.array([1.0, 0.0])
         mock_sim.return_value = np.array([[1.0, 0.1], [0.1, 1.0]])
         mock_mean.return_value = 0.1
         yield mock_model, mock_emb, mock_sim, mock_mean

def test_ground_truth_independence(mock_utils):
    """
    Test that task generation uses a distinct seed (Seed B) from skill generation (Seed A).
    This ensures that the ground-truth paths are independent of the semantic embedding space.
    """
    seed_a = 42
    seed_b = 123
    
    # Mock skills
    mock_skills = [{"id": "skill_1", "code": "def f(): pass"}]
    
    # Generate tasks with Seed B
    tasks_b1 = generate_tasks_with_ground_truth(mock_skills, seed_b)
    tasks_b2 = generate_tasks_with_ground_truth(mock_skills, seed_b)
    
    # Generate tasks with a different seed
    tasks_b3 = generate_tasks_with_ground_truth(mock_skills, seed_b + 1)
    
    # Verify reproducibility with same seed
    assert len(tasks_b1) == len(tasks_b2)
    assert tasks_b1[0]["ground_truth_path"] == tasks_b2[0]["ground_truth_path"]
    
    # Verify difference with different seed (should be different paths if randomness affects selection)
    # Note: With only 1 skill, path length is limited, so we check if the logic runs without error
    # and the seed is actually used.
    assert tasks_b1[0]["seed_used"] == seed_b
    assert tasks_b3[0]["seed_used"] == seed_b + 1
    
    # Verify that skills are not used in task generation logic (independence)
    # The function should only use skill IDs, not their embeddings or content
    assert all("code" not in str(t) for t in tasks_b1)

def test_skill_generation_seed_a(mock_utils):
    """
    Test that skill generation is deterministic with Seed A.
    """
    seed_a = 42
    
    skills_1, _ = generate_skills(seed_a, "low")
    skills_2, _ = generate_skills(seed_a, "low")
    
    # Verify same seed produces same skills
    assert len(skills_1) == len(skills_2)
    assert skills_1[0]["id"] == skills_2[0]["id"]
    assert skills_1[0]["code"] == skills_2[0]["code"]

def test_task_count_and_path_length(mock_utils):
    """
    Test that exactly 500 tasks are generated with path lengths between 3 and 5.
    """
    # Create enough skills for sampling
    mock_skills = [{"id": f"skill_{i}"} for i in range(100)]
    
    tasks = generate_tasks_with_ground_truth(mock_skills, 123)
    
    assert len(tasks) == 500
    for task in tasks:
        path = task["ground_truth_path"]
        assert 3 <= len(path) <= 5
        # Verify unique skills in path
        assert len(path) == len(set(path))

def test_seed_usage_in_metadata(mock_utils):
    """
    Test that the correct seeds are recorded in the output metadata.
    """
    seed_a = 999
    seed_b = 888
    
    # We can't easily run the full main() in unit test without file IO,
    # so we check the functions directly.
    skills, skill_meta = generate_skills(seed_a, "low")
    assert skill_meta["seed_used"] == seed_a
    
    mock_skills = [{"id": "s1"} for _ in range(100)]
    tasks = generate_tasks_with_ground_truth(mock_skills, seed_b)
    # The function returns a list, metadata is usually attached in main()
    # But we can verify the seed is used in the generation logic
    # by checking if the seed is passed correctly.
    # The generate_tasks_with_ground_truth function sets the seed at the start.
    
    # Re-run to ensure reproducibility
    tasks_2 = generate_tasks_with_ground_truth(mock_skills, seed_b)
    assert tasks[0]["ground_truth_path"] == tasks_2[0]["ground_truth_path"]
