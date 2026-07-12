"""
Unit tests for generate_data.py module.
Tests ground-truth independence between Seed A (skills) and Seed B (tasks).
"""
import json
import os
import random
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_data import (
    generate_skills,
    generate_tasks,
    validate_similarity_thresholds,
    SKILL_COUNT,
    TASK_COUNT,
)

# Mock the embedding functions to avoid actual model loading during tests
@pytest.fixture
def mock_embeddings():
    """Provide deterministic mock embeddings for testing."""
    def mock_get_embedding(text):
        # Create a deterministic embedding based on text length and hash
        h = hash(text) % 1000000
        return np.array([h % 100 / 100.0, (h // 100) % 100 / 100.0, 0.5])
    
    with patch('generate_data.get_embedding', side_effect=mock_get_embedding):
        yield mock_get_embedding

@pytest.fixture
def mock_seeds():
    """Provide fixed seeds for reproducibility."""
    return {"seed_a": 42, "seed_b": 123}

def test_skill_generation_deterministic(mock_seeds, mock_embeddings):
    """Test that skill generation is deterministic given the same seed."""
    seed_a = mock_seeds["seed_a"]
    
    # Generate skills twice with same seed
    skills1 = generate_skills(seed_a, count=10)
    skills2 = generate_skills(seed_a, count=10)
    
    # Verify they are identical
    assert len(skills1) == len(skills2)
    for s1, s2 in zip(skills1, skills2):
        assert s1["id"] == s2["id"]
        assert s1["code"] == s2["code"]
        assert s1["params"] == s2["params"]

def test_task_generation_deterministic(mock_seeds, mock_embeddings):
    """Test that task generation is deterministic given the same seed."""
    seed_b = mock_seeds["seed_b"]
    skills = generate_skills(mock_seeds["seed_a"], count=10)
    
    # Generate tasks twice with same seed
    tasks1 = generate_tasks(skills, seed_b, count=20)
    tasks2 = generate_tasks(skills, seed_b, count=20)
    
    # Verify they are identical
    assert len(tasks1) == len(tasks2)
    for t1, t2 in zip(tasks1, tasks2):
        assert t1["id"] == t2["id"]
        assert t1["description"] == t2["description"]
        assert t1["ground_truth_path"] == t2["ground_truth_path"]

def test_ground_truth_independence(mock_seeds, mock_embeddings):
    """
    Test that ground-truth paths are independent of skill embeddings.
    Tasks should use Seed B, skills use Seed A.
    Changing Seed A should not affect task ground-truth paths.
    """
    seed_b = mock_seeds["seed_b"]
    
    # Generate tasks with Seed A = 42
    skills_a1 = generate_skills(42, count=20)
    tasks_a1 = generate_tasks(skills_a1, seed_b, count=10)
    
    # Generate tasks with Seed A = 999 (different)
    skills_a2 = generate_skills(999, count=20)
    tasks_a2 = generate_tasks(skills_a2, seed_b, count=10)
    
    # Ground-truth paths should be identical because they depend only on Seed B
    for t1, t2 in zip(tasks_a1, tasks_a2):
        assert t1["ground_truth_path"] == t2["ground_truth_path"]

def test_ground_truth_independence_seed_b_change(mock_seeds, mock_embeddings):
    """
    Test that changing Seed B changes the ground-truth paths.
    """
    seed_a = mock_seeds["seed_a"]
    skills = generate_skills(seed_a, count=20)
    
    # Generate tasks with Seed B = 123
    tasks_b1 = generate_tasks(skills, 123, count=10)
    
    # Generate tasks with Seed B = 456
    tasks_b2 = generate_tasks(skills, 456, count=10)
    
    # Ground-truth paths should be different
    for t1, t2 in zip(tasks_b1, tasks_b2):
        assert t1["ground_truth_path"] != t2["ground_truth_path"]

def test_skill_count(mock_seeds, mock_embeddings):
    """Test that the correct number of skills is generated."""
    count = 100
    skills = generate_skills(mock_seeds["seed_a"], count=count)
    assert len(skills) == count

def test_task_count(mock_seeds, mock_embeddings):
    """Test that the correct number of tasks is generated."""
    count = 500
    skills = generate_skills(mock_seeds["seed_a"], count=100)
    tasks = generate_tasks(skills, mock_seeds["seed_b"], count=count)
    assert len(tasks) == count

def test_ground_truth_path_length(mock_seeds, mock_embeddings):
    """Test that ground-truth paths have 3-5 skill IDs."""
    skills = generate_skills(mock_seeds["seed_a"], count=100)
    tasks = generate_tasks(skills, mock_seeds["seed_b"], count=50)
    
    for task in tasks:
        path = task["ground_truth_path"]
        assert 3 <= len(path) <= 5
        assert len(path) == task["num_steps"]

def test_ground_truth_path_uniqueness(mock_seeds, mock_embeddings):
    """Test that each task has a unique ground-truth path."""
    skills = generate_skills(mock_seeds["seed_a"], count=100)
    tasks = generate_tasks(skills, mock_seeds["seed_b"], count=500)
    
    paths = [tuple(t["ground_truth_path"]) for t in tasks]
    assert len(paths) == len(set(paths)), "Duplicate ground-truth paths found"

def test_similarity_validation_low(mock_embeddings):
    """Test similarity validation for low overlap level."""
    # Create skills with low similarity (mocked)
    skills = generate_skills(42, count=20)
    validation = validate_similarity_thresholds(skills, "low")
    
    assert "mean_pairwise_similarity" in validation
    assert "is_valid" in validation
    assert "issues" in validation

def test_similarity_validation_medium(mock_embeddings):
    """Test similarity validation for medium overlap level."""
    skills = generate_skills(42, count=20)
    validation = validate_similarity_thresholds(skills, "medium")
    
    assert validation["target_level"] == "medium"
    assert "pct_above_05" in validation

def test_similarity_validation_high(mock_embeddings):
    """Test similarity validation for high overlap level."""
    skills = generate_skills(42, count=20)
    validation = validate_similarity_thresholds(skills, "high")
    
    assert validation["target_level"] == "high"
    assert "pct_above_08" in validation

def test_skill_code_format(mock_seeds, mock_embeddings):
    """Test that generated skills have valid code format."""
    skills = generate_skills(mock_seeds["seed_a"], count=10)
    
    for skill in skills:
        code = skill["code"]
        assert '"""' in code  # Has docstring
        assert "def " in code  # Has function definition
        assert skill["params"]["name"] in code  # Contains param name
