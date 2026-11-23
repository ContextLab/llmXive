import json
import os
import pytest
from pathlib import Path
from collections import Counter

# Import the module under test
from code.data.generate_perturbations import (
    generate_single_candidate,
    generate_and_filter_perturbations,
    BUDGET_CAP,
    MAX_CANDIDATES_PER_TASK,
    TRANSFORMATION_TYPES
)

@pytest.fixture
def sample_task():
    return {
        "task_id": "HumanEval/0",
        "prompt": "def add(a, b):\n    return a + b",
        "test": "assert add(1, 2) == 3",
        "entry_point": "add"
    }

@pytest.fixture
def sample_tasks(sample_task):
    return [sample_task, {
        "task_id": "HumanEval/1",
        "prompt": "def mul(a, b):\n    return a * b",
        "test": "assert mul(2, 3) == 6",
        "entry_point": "mul"
    }]

def test_generate_single_candidate_synonym(sample_task):
    """Test that a synonym perturbation is generated correctly."""
    candidate = generate_single_candidate(sample_task, "synonym", None)
    assert candidate["task_id"] == "HumanEval/0"
    assert candidate["perturbation_type"] == "synonym"
    assert "candidate_text" in candidate
    assert candidate["raw_score"] == 0.0  # Placeholder
    assert candidate["is_valid"] is False  # Placeholder

def test_generate_single_candidate_typo(sample_task):
    """Test that a typo perturbation is generated correctly."""
    candidate = generate_single_candidate(sample_task, "typo", None)
    assert candidate["task_id"] == "HumanEval/0"
    assert candidate["perturbation_type"] == "typo"
    assert "candidate_text" in candidate

def test_generate_single_candidate_rephrase(sample_task):
    """Test that a rephrase perturbation is generated correctly."""
    candidate = generate_single_candidate(sample_task, "rephrase", None)
    assert candidate["task_id"] == "HumanEval/0"
    assert candidate["perturbation_type"] == "rephrase"
    assert "candidate_text" in candidate

def test_generate_and_filter_perturbations_limit(sample_tasks, caplog):
    """Test that generation respects the max candidates per task limit."""
    # Mock logger to avoid None issues in test
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): pass
    
    logger = MockLogger()
    candidates = generate_and_filter_perturbations(sample_tasks, logger)
    
    # Count candidates per task
    counts = Counter(c["task_id"] for c in candidates)
    
    # Verify no task exceeds 3 candidates
    for task_id, count in counts.items():
        assert count <= MAX_CANDIDATES_PER_TASK, f"Task {task_id} has {count} candidates, max is {MAX_CANDIDATES_PER_TASK}"

def test_transformation_types_order():
    """Verify that transformation types are sorted alphabetically."""
    expected = ["rephrase", "synonym", "typo"]
    assert TRANSFORMATION_TYPES == expected, "Transformation types must be sorted alphabetically for determinism"

def test_schema_structure(sample_task):
    """Verify the output schema matches the requirement."""
    candidate = generate_single_candidate(sample_task, "synonym", None)
    
    required_keys = {"task_id", "perturbation_type", "raw_score", "is_valid", "candidate_text"}
    assert set(candidate.keys()) == required_keys, f"Missing keys in schema: {required_keys - set(candidate.keys())}"
    
    assert isinstance(candidate["task_id"], str)
    assert isinstance(candidate["perturbation_type"], str)
    assert isinstance(candidate["raw_score"], float)
    assert isinstance(candidate["is_valid"], bool)
    assert isinstance(candidate["candidate_text"], str)
    
    assert candidate["perturbation_type"] in ["synonym", "typo", "rephrase"]
