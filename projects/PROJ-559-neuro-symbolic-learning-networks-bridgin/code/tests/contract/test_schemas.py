import pytest
import json
import os
import sys
from utils.validation import validate_explanation, validate_problem, validate_simulation_log

class TestExplanationSchema:
    """Contract tests for explanation schema validation."""

    def test_valid_explanation_structure(self):
        """Test that a valid explanation passes schema validation."""
        valid_explanation = {
            "problem_id": "prob_001",
            "explanation_type": "neural",
            "text": "To solve this problem, we first identify the known values and then apply the relevant formula.",
            "confidence_score": 0.92
        }
        assert validate_explanation(valid_explanation) is True

    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        incomplete_explanation = {
            "problem_id": "prob_001",
            "explanation_type": "neural"
        }
        assert validate_explanation(incomplete_explanation) is False

    def test_invalid_explanation_type(self):
        """Test that invalid explanation types fail validation."""
        invalid_explanation = {
            "problem_id": "prob_001",
            "explanation_type": "invalid_type",
            "text": "Some text",
            "confidence_score": 0.85
        }
        assert validate_explanation(invalid_explanation) is False


class TestProblemSchema:
    """Contract tests for problem schema validation."""

    def test_valid_problem_structure(self):
        """Test that a valid problem passes schema validation."""
        valid_problem = {
            "problem_id": "prob_001",
            "question": "What is 2 + 2?",
            "answer": 4,
            "difficulty": "easy",
            "category": "arithmetic"
        }
        assert validate_problem(valid_problem) is True

    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        incomplete_problem = {
            "problem_id": "prob_001",
            "question": "What is 2 + 2?"
        }
        assert validate_problem(incomplete_problem) is False

    def test_invalid_difficulty(self):
        """Test that invalid difficulty values fail validation."""
        invalid_problem = {
            "problem_id": "prob_001",
            "question": "What is 2 + 2?",
            "answer": 4,
            "difficulty": "unknown",
            "category": "arithmetic"
        }
        assert validate_problem(invalid_problem) is False


class TestSimulationLogSchema:
    """Contract tests for SimulationLog schema validation."""

    def test_valid_simulation_log_structure(self):
        """Test that a valid simulation log passes schema validation."""
        valid_log = {
            "student_id": "student_001",
            "problem_id": "prob_001",
            "condition": "neural",
            "correct": True,
            "rt_seconds": 5.2,
            "comprehension_rating": 4,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        assert validate_simulation_log(valid_log) is True

    def test_missing_required_fields(self):
        """Test that missing required fields fail validation."""
        incomplete_log = {
            "student_id": "student_001",
            "problem_id": "prob_001",
            "condition": "neural"
        }
        assert validate_simulation_log(incomplete_log) is False

    def test_invalid_condition(self):
        """Test that invalid condition values fail validation."""
        invalid_log = {
            "student_id": "student_001",
            "problem_id": "prob_001",
            "condition": "invalid_condition",
            "correct": True,
            "rt_seconds": 5.2,
            "comprehension_rating": 4,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        assert validate_simulation_log(invalid_log) is False

    def test_invalid_comprehension_rating(self):
        """Test that comprehension rating outside 1-5 range fails validation."""
        invalid_log = {
            "student_id": "student_001",
            "problem_id": "prob_001",
            "condition": "neural",
            "correct": True,
            "rt_seconds": 5.2,
            "comprehension_rating": 6,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        assert validate_simulation_log(invalid_log) is False

    def test_invalid_response_time(self):
        """Test that negative response time fails validation."""
        invalid_log = {
            "student_id": "student_001",
            "problem_id": "prob_001",
            "condition": "neural",
            "correct": True,
            "rt_seconds": -1.0,
            "comprehension_rating": 4,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        assert validate_simulation_log(invalid_log) is False

    def test_missing_timestamp(self):
        """Test that missing timestamp fails validation."""
        invalid_log = {
            "student_id": "student_001",
            "problem_id": "prob_001",
            "condition": "neural",
            "correct": True,
            "rt_seconds": 5.2,
            "comprehension_rating": 4
        }
        assert validate_simulation_log(invalid_log) is False