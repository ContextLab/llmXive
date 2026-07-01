"""
Unit tests for ReferenceValidatorAgent.
"""

import pytest
from src.validators.reference_validator import (
    ReferenceValidatorAgent,
    tokenize_text,
    compute_title_token_overlap,
    validate_constitution_ii,
    TITLE_TOKEN_OVERLAP_THRESHOLD
)


class TestTokenizeTitle:
    """Tests for tokenize_text function."""

    def test_simple_tokenization(self):
        tokens = tokenize_text("Hello World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty_string(self):
        tokens = tokenize_text("")
        assert tokens == []

    def test_special_characters(self):
        tokens = tokenize_text("Hello, World! 123")
        assert "hello" in tokens
        assert "world" in tokens
        assert "123" in tokens

    def test_case_insensitivity(self):
        tokens = tokenize_text("HELLO hello HeLLo")
        assert len(tokens) == 3
        assert all(t == "hello" for t in tokens)


class TestComputeTitleTokenOverlap:
    """Tests for compute_title_token_overlap function."""

    def test_identical_titles(self):
        overlap = compute_title_token_overlap("Test Title", "Test Title")
        assert overlap == 1.0

    def test_no_overlap(self):
        overlap = compute_title_token_overlap("Apple", "Banana")
        assert overlap == 0.0

    def test_partial_overlap(self):
        # "A B C" vs "B C D" -> intersection {B,C}, union {A,B,C,D} -> 2/4 = 0.5
        overlap = compute_title_token_overlap("A B C", "B C D")
        assert overlap == 0.5

    def test_empty_titles(self):
        overlap = compute_title_token_overlap("", "")
        assert overlap == 0.0

    def test_one_empty_title(self):
        overlap = compute_title_token_overlap("Test", "")
        assert overlap == 0.0


class TestValidateRefe:
    """Tests for validate_constitution_ii function."""

    def test_compliant_data(self):
        data = {
            "metrics": {"accuracy": {"value": 0.9, "fabricated": False}},
            "data_sources": [{"name": "RealDataset", "type": "real"}],
            "methodology": "Standard procedure"
        }
        is_compliant, violations = validate_constitution_ii(data)
        assert is_compliant
        assert violations == []

    def test_fabrication_detected(self):
        data = {
            "metrics": {"accuracy": {"value": 0.9, "fabricated": True}},
            "data_sources": [{"name": "RealDataset", "type": "real"}],
            "methodology": "Standard procedure"
        }
        is_compliant, violations = validate_constitution_ii(data)
        assert not is_compliant
        assert any("Fabricated" in v for v in violations)

    def test_missing_data_sources(self):
        data = {
            "metrics": {"accuracy": {"value": 0.9}},
            "methodology": "Standard procedure"
        }
        is_compliant, violations = validate_constitution_ii(data)
        assert not is_compliant
        assert any("No data sources" in v for v in violations)

    def test_missing_methodology(self):
        data = {
            "metrics": {"accuracy": {"value": 0.9}},
            "data_sources": [{"name": "RealDataset", "type": "real"}]
        }
        is_compliant, violations = validate_constitution_ii(data)
        assert not is_compliant
        assert any("Missing methodology" in v for v in violations)


class TestReferenceValidatorAgent:
    """Tests for ReferenceValidatorAgent class."""

    def test_init(self):
        validator = ReferenceValidatorAgent("Test Title")
        assert validator.reference_title == "Test Title"

    def test_high_overlap_passes(self):
        validator = ReferenceValidatorAgent("Scientific Benchmark Model")
        data = {
            "metrics": {"acc": {"value": 0.9}},
            "data_sources": [{"name": "DS", "type": "real"}],
            "methodology": "Test"
        }
        result = validator.validate_contribution("Scientific Benchmark Model", data)
        assert result["passed"]
        assert result["title_overlap_score"] == 1.0
        assert result["review_points"] == 1

    def test_low_overlap_blocks(self):
        validator = ReferenceValidatorAgent("Scientific Benchmark Model")
        data = {
            "metrics": {"acc": {"value": 0.9}},
            "data_sources": [{"name": "DS", "type": "real"}],
            "methodology": "Test"
        }
        result = validator.validate_contribution("Completely Different Topic", data)
        assert not result["passed"]
        assert result["review_points"] == 0
        assert "blocked_reason" in result
        assert result["blocked_reason"].startswith("Title overlap")

    def test_constitution_failure_blocks(self):
        validator = ReferenceValidatorAgent("Scientific Benchmark Model")
        data = {
            "metrics": {"acc": {"value": 0.9, "fabricated": True}},
            "data_sources": [{"name": "DS", "type": "real"}],
            "methodology": "Test"
        }
        result = validator.validate_contribution("Scientific Benchmark Model", data)
        assert not result["passed"]
        assert result["review_points"] == 0
        assert "blocked_reason" in result
        assert "Constitution II" in result["blocked_reason"]

    def test_get_review_points(self):
        validator = ReferenceValidatorAgent("Test Title")
        data = {
            "metrics": {"acc": {"value": 0.9}},
            "data_sources": [{"name": "DS", "type": "real"}],
            "methodology": "Test"
        }
        points = validator.get_review_points("Test Title", data)
        assert points == 1

        bad_data = {
            "metrics": {"acc": {"value": 0.9, "fabricated": True}},
            "data_sources": [{"name": "DS", "type": "real"}],
            "methodology": "Test"
        }
        points_bad = validator.get_review_points("Test Title", bad_data)
        assert points_bad == 0
