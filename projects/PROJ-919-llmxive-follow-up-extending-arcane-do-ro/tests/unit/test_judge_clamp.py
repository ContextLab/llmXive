"""
Unit tests for Judge output format and clamping logic.

This test module verifies that the Judge service:
1. Produces output adhering to the expected JSON schema.
2. Correctly clamps scores to the defined Likert scale (1-5).
3. Returns the `adherence_flag` boolean alongside the score.
"""

import pytest
import json
import sys
from pathlib import Path

# Add project root to path if running as script
if str(Path(__file__).resolve().parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.services.judge_service import (
    clamp_score,
    validate_judge_output,
    extract_score_and_flag
)


class TestJudgeClamping:
    """Tests for score clamping logic."""

    def test_clamp_score_below_minimum(self):
        """Scores below 1 should be clamped to 1."""
        assert clamp_score(0.0) == 1.0
        assert clamp_score(-5.0) == 1.0
        assert clamp_score(-0.001) == 1.0

    def test_clamp_score_above_maximum(self):
        """Scores above 5 should be clamped to 5."""
        assert clamp_score(5.001) == 5.0
        assert clamp_score(10.0) == 5.0
        assert clamp_score(100.0) == 5.0

    def test_clamp_score_within_range(self):
        """Scores within 1-5 should remain unchanged."""
        assert clamp_score(1.0) == 1.0
        assert clamp_score(3.5) == 3.5
        assert clamp_score(5.0) == 5.0
        assert clamp_score(2.75) == 2.75

    def test_clamp_score_integer_input(self):
        """Integer inputs within range should be preserved or converted to float."""
        assert clamp_score(3) == 3.0
        assert clamp_score(1) == 1.0
        assert clamp_score(5) == 5.0


class TestJudgeOutputValidation:
    """Tests for Judge output format validation."""

    def test_validate_judge_output_valid(self):
        """Valid output should return True."""
        valid_output = {
            "score": 4.0,
            "adherence_flag": True,
            "reasoning": "The response aligns well with the character arc."
        }
        assert validate_judge_output(valid_output) is True

    def test_validate_judge_output_missing_score(self):
        """Output missing 'score' should return False."""
        invalid_output = {
            "adherence_flag": True,
            "reasoning": "Good response."
        }
        assert validate_judge_output(invalid_output) is False

    def test_validate_judge_output_missing_flag(self):
        """Output missing 'adherence_flag' should return False."""
        invalid_output = {
            "score": 4.0,
            "reasoning": "Good response."
        }
        assert validate_judge_output(invalid_output) is False

    def test_validate_judge_output_wrong_type_score(self):
        """Output with non-numeric score should return False."""
        invalid_output = {
            "score": "high",
            "adherence_flag": True
        }
        assert validate_judge_output(invalid_output) is False

    def test_validate_judge_output_wrong_type_flag(self):
        """Output with non-boolean flag should return False."""
        invalid_output = {
            "score": 4.0,
            "adherence_flag": "yes"
        }
        assert validate_judge_output(invalid_output) is False

    def test_validate_judge_output_out_of_range_score(self):
        """Output with score outside 1-5 should be caught (clamping happens elsewhere, but validation checks bounds)."""
        # Note: validate_judge_output checks schema/types, clamping is a separate step.
        # However, logically, a valid *final* output should be in range.
        # We test that the validator accepts the structure, even if the value is extreme,
        # assuming clamping is applied before final validation or as part of the pipeline.
        # Based on typical design, validation checks structure; clamping checks value.
        # Let's assume validate_judge_output checks structure + range constraints per FR-004.
        invalid_output = {
            "score": 10.0,
            "adherence_flag": True
        }
        # If validation includes range check:
        assert validate_judge_output(invalid_output) is False


class TestExtractScoreAndFlag:
    """Tests for extracting score and flag from raw LLM output."""

    def test_extract_score_and_flag_valid_json(self):
        """Valid JSON string should be parsed correctly."""
        raw_output = json.dumps({
            "score": 4.0,
            "adherence_flag": False,
            "reasoning": "Test"
        })
        score, flag = extract_score_and_flag(raw_output)
        assert score == 4.0
        assert flag is False

    def test_extract_score_and_flag_malformed_json(self):
        """Malformed JSON should raise ValueError."""
        raw_output = '{"score": 4.0, "adherence_flag": true'
        with pytest.raises(ValueError):
            extract_score_and_flag(raw_output)

    def test_extract_score_and_flag_missing_fields(self):
        """Missing required fields should raise KeyError/ValueError."""
        raw_output = json.dumps({"score": 4.0})
        with pytest.raises((KeyError, ValueError)):
            extract_score_and_flag(raw_output)

    def test_extract_score_and_flag_clamps_result(self):
        """Extracted score should be clamped even if raw JSON had out-of-range value."""
        raw_output = json.dumps({
            "score": 100.0,
            "adherence_flag": True
        })
        score, flag = extract_score_and_flag(raw_output)
        assert score == 5.0  # Clamped
        assert flag is True