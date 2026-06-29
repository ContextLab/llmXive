"""
Contract tests for explanation schema validation.
Tests that the validation utilities correctly enforce the schema definitions
for explanation artifacts as defined in contracts/.
"""

import pytest
import json
import os
import sys

# Ensure project root is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from utils.validation import validate_explanation, validate_problem


class TestExplanationSchema:
    """Tests for the explanation schema validation logic."""

    def test_valid_neural_explanation(self, tmp_path):
        """Validate a correctly formed neural explanation."""
        data = {
            "problem_id": "prob_001",
            "type": "neural",
            "explanation_text": "The model suggests the answer is 4 based on pattern matching.",
            "confidence": 0.85,
            "model_version": "tinyllama-1.1b-v1",
            "generated_at": "2026-01-01T00:00:00Z"
        }
        path = tmp_path / "neural_exp.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_symbolic_explanation(self, tmp_path):
        """Validate a correctly formed symbolic explanation."""
        data = {
            "problem_id": "prob_001",
            "type": "symbolic",
            "explanation_text": "Using commutativity: a + b = b + a.",
            "trace": [
                {"rule": "commutativity", "operands": ["a", "b"]},
                {"rule": "identity", "operands": ["result"]}
            ],
            "confidence": 1.0,
            "generated_at": "2026-01-01T00:00:00Z"
        }
        path = tmp_path / "symbolic_exp.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_neuro_symbolic_explanation(self, tmp_path):
        """Validate a correctly formed neuro-symbolic explanation."""
        data = {
            "problem_id": "prob_001",
            "type": "neuro_symbolic",
            "neural_narrative": "The pattern suggests addition.",
            "symbolic_trace": [
                {"rule": "associativity", "operands": ["a", "b", "c"]}
            ],
            "confidence": 0.92,
            "generated_at": "2026-01-01T00:00:00Z"
        }
        path = tmp_path / "neuro_symbolic_exp.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field_type(self, tmp_path):
        """Validation should fail if 'type' is missing."""
        data = {
            "problem_id": "prob_001",
            "explanation_text": "Some text",
            "confidence": 0.5
        }
        path = tmp_path / "invalid_exp.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is False
        assert any("type" in str(e).lower() for e in errors)

    def test_invalid_type_value(self, tmp_path):
        """Validation should fail if 'type' is not one of the allowed values."""
        data = {
            "problem_id": "prob_001",
            "type": "unknown_type",
            "explanation_text": "Text",
            "confidence": 0.5
        }
        path = tmp_path / "invalid_type.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is False
        assert any("type" in str(e).lower() for e in errors)

    def test_missing_problem_id(self, tmp_path):
        """Validation should fail if problem_id is missing."""
        data = {
            "type": "neural",
            "explanation_text": "Text",
            "confidence": 0.5
        }
        path = tmp_path / "no_id.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is False
        assert any("problem_id" in str(e).lower() for e in errors)

    def test_symbolic_missing_trace(self, tmp_path):
        """Symbolic explanations must have a trace."""
        data = {
            "problem_id": "prob_001",
            "type": "symbolic",
            "explanation_text": "Text",
            "confidence": 1.0
        }
        path = tmp_path / "no_trace.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is False
        assert any("trace" in str(e).lower() for e in errors)

    def test_file_not_found(self, tmp_path):
        """Validation should handle missing files gracefully."""
        is_valid, errors = validate_explanation(str(tmp_path / "nonexistent.json"))
        assert is_valid is False
        assert any("not found" in str(e).lower() or "file" in str(e).lower() for e in errors)

    def test_invalid_json(self, tmp_path):
        """Validation should handle malformed JSON."""
        path = tmp_path / "bad.json"
        with open(path, 'w') as f:
            f.write("{ this is not valid json }")

        is_valid, errors = validate_explanation(str(path))
        assert is_valid is False
        assert any("json" in str(e).lower() for e in errors)


class TestProblemSchema:
    """Tests for the problem schema validation logic (supporting explanations)."""

    def test_valid_problem(self, tmp_path):
        """Validate a correctly formed problem definition."""
        data = {
            "problem_id": "prob_001",
            "question": "What is 2 + 2?",
            "answer": 4,
            "difficulty": 1,
            "subject": "arithmetic"
        }
        path = tmp_path / "prob.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_problem(str(path))
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_question(self, tmp_path):
        """Problem must have a question field."""
        data = {
            "problem_id": "prob_001",
            "answer": 4
        }
        path = tmp_path / "no_q.json"
        with open(path, 'w') as f:
            json.dump(data, f)

        is_valid, errors = validate_problem(str(path))
        assert is_valid is False
        assert any("question" in str(e).lower() for e in errors)