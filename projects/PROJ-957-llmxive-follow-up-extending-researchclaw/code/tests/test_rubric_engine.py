"""
Tests for the Rubric Engine.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scoring.rubric_engine import RubricEngine


class TestRubricEngine:
    """Tests for the RubricEngine class."""

    @pytest.fixture
    def sample_schema(self, tmp_path):
        """Create a temporary schema file."""
        schema = {
            "rubrics": {
                "Protocol Alignment": {
                    "criteria": [
                        {"key": "step_1", "weight": 0.5},
                        {"key": "step_2", "weight": 0.5}
                    ]
                }
            },
            "threshold_high": 40,
            "threshold_low": 10,
            "feature_extraction_method": "regex_match"
        }
        schema_path = tmp_path / "test_schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema, f)
        return str(schema_path)

    def test_load_schema(self, sample_schema):
        """Test that the schema loads correctly."""
        engine = RubricEngine(schema_path=sample_schema)
        assert "rubrics" in engine.schema
        assert "Protocol Alignment" in engine.schema["rubrics"]

    def test_extract_feature_found(self, sample_schema):
        """Test feature extraction when key is found."""
        engine = RubricEngine(schema_path=sample_schema)
        text = "### step_1\nThis is the first step."
        result = engine._extract_feature(text, "step_1")
        assert result == 1.0

    def test_extract_feature_not_found(self, sample_schema):
        """Test feature extraction when key is not found."""
        engine = RubricEngine(schema_path=sample_schema)
        text = "This text has no steps."
        result = engine._extract_feature(text, "step_1")
        assert result == 0.0

    def test_calculate_rubric_score_partial(self, sample_schema):
        """Test scoring with partial matches."""
        engine = RubricEngine(schema_path=sample_schema)
        # Only step_1 is present (weight 0.5)
        text = "### step_1\nFirst step here."
        score = engine.calculate_rubric_score("Protocol Alignment", text)
        # 0.5 * 1.0 + 0.5 * 0.0 = 0.5 -> 50% of max
        assert score == 50.0

    def test_calculate_rubric_score_full(self, sample_schema):
        """Test scoring with full matches."""
        engine = RubricEngine(schema_path=sample_schema)
        text = "### step_1\nFirst step. ### step_2\nSecond step."
        score = engine.calculate_rubric_score("Protocol Alignment", text)
        # 0.5 * 1.0 + 0.5 * 1.0 = 1.0 -> 100% of max
        assert score == 100.0

    def test_calculate_rubric_score_empty(self, sample_schema):
        """Test scoring with no matches."""
        engine = RubricEngine(schema_path=sample_schema)
        text = "Random text."
        score = engine.calculate_rubric_score("Protocol Alignment", text)
        assert score == 0.0

    def test_evaluate_status_pass(self, sample_schema):
        """Test evaluation returning 'pass' status."""
        engine = RubricEngine(schema_path=sample_schema)
        # High score should trigger pass
        text = "### step_1\nStep 1. ### step_2\nStep 2."
        result = engine.evaluate(text)
        assert result["status"] == "pass"
        assert result["total_score"] == 100.0

    def test_evaluate_status_fail(self, sample_schema):
        """Test evaluation returning 'fail' status."""
        engine = RubricEngine(schema_path=sample_schema)
        # Low score should trigger fail
        text = "Random text."
        result = engine.evaluate(text)
        assert result["status"] == "fail"
        assert result["total_score"] == 0.0

    def test_invalid_rubric_name(self, sample_schema):
        """Test error handling for invalid rubric name."""
        engine = RubricEngine(schema_path=sample_schema)
        with pytest.raises(ValueError, match="not found in schema"):
            engine.calculate_rubric_score("Invalid Rubric", "text")