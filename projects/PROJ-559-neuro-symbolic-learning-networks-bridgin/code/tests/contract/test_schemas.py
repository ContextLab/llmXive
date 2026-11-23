import pytest
import json
import os
import sys
from pathlib import Path

# Add root to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.validation import validate_explanation, validate_problem, validate_simulation_log

class TestExplanationSchema:
    """Contract tests for Explanation schema validation."""

    def test_valid_explanation_structure(self):
        """Test that a valid explanation passes schema validation."""
        valid_exp = {
            "explanation_id": "exp_001",
            "problem_id": "prob_001",
            "condition": "neural",
            "text": "Here is a step-by-step explanation of the solution.",
            "symbolic_trace": [
                {"rule": "commutativity", "step": 1, "result": "a + b = b + a"}
            ],
            "neural_narrative": "The model identified the pattern and generated a fluent response.",
            "generated_at": "2024-01-15T10:30:00Z"
        }
        assert validate_explanation(valid_exp) is True

    def test_missing_field_explanation(self):
        """Test that missing required fields fail validation."""
        invalid_exp = {
            "explanation_id": "exp_002",
            # Missing problem_id, condition, text, etc.
        }
        assert validate_explanation(invalid_exp) is False

class TestProblemSchema:
    """Contract tests for Problem schema validation."""

    def test_valid_problem_structure(self):
        """Test that a valid problem passes schema validation."""
        valid_prob = {
            "problem_id": "prob_001",
            "subject": "math",
            "topic": "arithmetic",
            "difficulty": 2,
            "question_text": "What is 2 + 3?",
            "correct_answer": "5"
        }
        assert validate_problem(valid_prob) is True

    def test_invalid_problem_type(self):
        """Test that wrong types fail validation."""
        invalid_prob = {
            "problem_id": 123, # Should be string
            "subject": "math",
            "topic": "arithmetic",
            "difficulty": "easy", # Should be int
            "question_text": "What is 2 + 3?",
            "correct_answer": "5"
        }
        assert validate_problem(invalid_prob) is False

class TestSimulationLogSchema:
    """Contract tests for SimulationLog schema validation."""

    def test_valid_simulation_log_structure(self):
        """Test that a valid simulation log entry passes validation."""
        valid_log = {
            "student_id": "student_neural_0001",
            "condition": "neural",
            "problem_id": "prob_001",
            "attempt": 0,
            "timestamp": "2024-01-15T10:30:00Z",
            "knowledge_state": 0.85,
            "correct": True,
            "rt_seconds": 12.5,
            "comprehension_rating": 4,
            "data_source": "simulated"
        }
        assert validate_simulation_log(valid_log) is True

    def test_missing_field_simulation_log(self):
        """Test that missing required fields fail validation."""
        invalid_log = {
            "student_id": "student_neural_0002",
            "condition": "neural",
            # Missing problem_id, attempt, etc.
        }
        assert validate_simulation_log(invalid_log) is False

    def test_invalid_types_simulation_log(self):
        """Test that invalid types fail validation."""
        invalid_log = {
            "student_id": "student_neural_0003",
            "condition": "neural",
            "problem_id": "prob_001",
            "attempt": "first", # Should be int
            "timestamp": "2024-01-15T10:30:00Z",
            "knowledge_state": "high", # Should be float
            "correct": "yes", # Should be bool
            "rt_seconds": 12.5,
            "comprehension_rating": 4,
            "data_source": "simulated"
        }
        assert validate_simulation_log(invalid_log) is False
