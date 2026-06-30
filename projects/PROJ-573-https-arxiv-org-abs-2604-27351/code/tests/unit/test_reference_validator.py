"""
Unit tests for the Reference Validator Agent.
"""

import pytest
from src.validators.reference_validator import (
    tokenize_title,
    compute_title_token_overlap,
    validate_reference_title_overlap,
    check_constitution_ii_compliance,
    ReferenceValidatorAgent
)


class TestTokenizeTitle:
    def test_basic_tokenization(self):
        title = "Deep Learning for Time Series"
        tokens = tokenize_title(title)
        assert "deep" in tokens
        assert "learning" in tokens
        assert "time" in tokens
        assert "series" in tokens
        assert "for" not in tokens  # Filtered out as short

    def test_punctuation_removal(self):
        title = "Hello, World! How are you?"
        tokens = tokenize_title(title)
        assert "," not in tokens
        assert "!" not in tokens
        assert "hello" in tokens

    def test_empty_title(self):
        assert tokenize_title("") == set()
        assert tokenize_title(None) == set()


class TestComputeTitleTokenOverlap:
    def test_identical_titles(self):
        score = compute_title_token_overlap("Test Title", "Test Title")
        assert score == 1.0

    def test_no_overlap(self):
        score = compute_title_token_overlap("Cat Dog", "Bird Fish")
        assert score == 0.0

    def test_partial_overlap(self):
        # "Deep Learning" vs "Deep Learning for Time"
        # Tokens: {deep, learning} vs {deep, learning, time}
        # Intersection: 2, Union: 3 -> 2/3
        score = compute_title_token_overlap("Deep Learning", "Deep Learning for Time")
        assert abs(score - 0.666) < 0.01


class TestValidateReferenceTitleOverlap:
    def test_passes_threshold(self):
        title = "Deep Learning for Time Series"
        known = ["Deep Learning for Time Series Forecasting"]
        is_valid, score, _ = validate_reference_title_overlap(title, known)
        # Should be high overlap
        assert is_valid is True
        assert score >= 0.7

    def test_fails_threshold(self):
        title = "Completely Different Topic"
        known = ["Deep Learning for Time Series"]
        is_valid, score, _ = validate_reference_title_overlap(title, known)
        assert is_valid is False
        assert score < 0.7


class TestCheckConstitutionIICompliance:
    def test_compliant(self):
        data = {
            "title": "Test",
            "abstract": "Test abstract",
            "authors": ["Author"],
            "year": 2023,
            "doi": "10.1234/test"
        }
        is_compliant, missing = check_constitution_ii_compliance(data)
        assert is_compliant is True
        assert len(missing) == 0

    def test_missing_fields(self):
        data = {
            "title": "Test",
            # Missing others
        }
        is_compliant, missing = check_constitution_ii_compliance(data)
        assert is_compliant is False
        assert "abstract" in missing
        assert "authors" in missing


class TestReferenceValidatorAgent:
    @pytest.fixture
    def agent(self):
        return ReferenceValidatorAgent(known_titles=["Deep Learning Survey"])

    def test_valid_reference(self, agent):
        ref = {
            "title": "Deep Learning Survey Update",
            "abstract": "New survey",
            "authors": ["A"],
            "year": 2024,
            "doi": "10.1234/doi"
        }
        result = agent.validate_reference(ref)
        assert result["allowed"] is True
        assert result["constitution_valid"] is True
        assert result["overlap_valid"] is True

    def test_invalid_constitution(self, agent):
        ref = {
            "title": "Test",
            # Missing fields
        }
        result = agent.validate_reference(ref)
        assert result["allowed"] is False
        assert result["constitution_valid"] is False

    def test_low_overlap(self, agent):
        ref = {
            "title": "Unrelated Topic",
            "abstract": "No relation",
            "authors": ["A"],
            "year": 2024,
            "doi": "10.1234/doi"
        }
        result = agent.validate_reference(ref)
        assert result["allowed"] is False
        assert result["overlap_valid"] is False

    def test_add_known_title(self, agent):
        agent.add_known_title("New Title")
        assert "New Title" in agent.known_titles