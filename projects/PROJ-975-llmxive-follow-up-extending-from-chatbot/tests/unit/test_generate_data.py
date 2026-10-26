import json
import os
import sys
import pathlib
import pytest
import numpy as np

# Ensure the code directory is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from generate_data import (
    generate_skills,
    generate_tasks,
    validate_similarity_thresholds,
    SKILL_COUNT,
    TASK_COUNT,
)

def test_skill_generation_deterministic():
    """Test that skill generation is deterministic given the same seed."""
    seed = 42
    skills1 = generate_skills(seed, count=10)
    skills2 = generate_skills(seed, count=10)
    assert skills1 == skills2

def test_task_generation_deterministic():
    """Test that task generation is deterministic given the same seed."""
    seed = 42
    skills = generate_skills(seed, count=10)
    tasks1 = generate_tasks(seed, skills, count=20)
    tasks2 = generate_tasks(seed, skills, count=20)
    assert tasks1 == tasks2

def test_ground_truth_independence():
    """Changing Skill Seed should not change Task ground-truth paths (Seed B)."""
    seed_b = 123
    skills_a1 = generate_skills(42, count=20)
    tasks_a1 = generate_tasks(seed_b, skills_a1, count=10)

    skills_a2 = generate_skills(999, count=20)
    tasks_a2 = generate_tasks(seed_b, skills_a2, count=10)

    for t1, t2 in zip(tasks_a1, tasks_a2):
        assert t1["ground_truth_path"] == t2["ground_truth_path"]

def test_skill_count():
    skills = generate_skills(42, count=SKILL_COUNT)
    assert len(skills) == SKILL_COUNT

def test_task_count():
    skills = generate_skills(42, count=100)
    tasks = generate_tasks(123, skills, count=TASK_COUNT)
    assert len(tasks) == TASK_COUNT

def test_ground_truth_path_validity():
    skills = generate_skills(42, count=100)
    tasks = generate_tasks(123, skills, count=50)
    for task in tasks:
        path = task["ground_truth_path"]
        assert 3 <= len(path) <= 5
        assert task["solution_path"] == path

def test_similarity_validation_high():
    skills = generate_skills(42, count=20, overlap_level="high")
    validation = validate_similarity_thresholds(skills, "high")
    assert validation["is_valid"]

def test_similarity_validation_low():
    skills = generate_skills(42, count=20, overlap_level="low")
    validation = validate_similarity_thresholds(skills, "low")
    assert validation["is_valid"]