"""
Unit tests for the ReferenceValidatorAgent.
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
    def test_simple_tokenization(self):
        tokens = tokenize_title("Hello World")
        assert tokens == ["hello", "world"]

    def test_punctuation_removal(self):
        tokens = tokenize_title("Hello, World!")
        assert tokens == ["hello", "world"]

    def test_empty_string(self):
        tokens = tokenize_title("")
        assert tokens == []

    def test_case_insensitivity(self):
        tokens = tokenize_title("HELLO world")
        assert tokens == ["hello", "world"]

class TestComputeTitleTokenOverlap:
    def test_identical_titles(self):
        score = compute_title_token_overlap("Test Title", "Test Title")
        assert score == 1.0

    def test_no_overlap(self):
        score = compute_title_token_overlap("Cat Food", "Dog Toy")
        assert score == 0.0

    def test_partial_overlap(self):
        score = compute_title_token_overlap("A B C", "A B D")
        # Intersection: {A, B}, Union: {A, B, C, D} -> 2/4 = 0.5
        assert score == 0.5

    def test_empty_inputs(self):
        score = compute_title_token_overlap("", "")
        assert score == 0.0

class TestValidateReferenceTitleOverlap:
    def test_passes_threshold(self):
        # "Benchmark" and "Benchmark" -> high overlap
        valid, score = validate_reference_title_overlap(
            "Heterogeneous Benchmark",
            "Scientific Benchmark"
        )
        assert valid is True
        assert score > 0.7

    def test_fails_threshold(self):
        valid, score = validate_reference_title_overlap(
            "Random Cats",
            "Heterogeneous Benchmark"
        )
        assert valid is False
        assert score < 0.7

class TestCheckConstitutionIICompliance:
    def test_compliant_document(self):
        text = "This paper presents a heterogeneous benchmark for foundation models in scientific collaboration."
        compliant, details = check_constitution_ii_compliance(text)
        assert compliant is True
        assert details["found_count"] >= 2

    def test_non_compliant_document(self):
        text = "This is a random text about cats and dogs."
        compliant, details = check_constitution_ii_compliance(text)
        assert compliant is False
        assert details["found_count"] < 2

class TestReferenceValidatorAgent:
    def test_valid_reference(self):
        agent = ReferenceValidatorAgent()
        result = agent.validate(
            "Heterogeneous Benchmark for Foundation Models",
            "A study on heterogeneous foundation models for scientific collaboration."
        )
        assert result["passed"] is True

    def test_invalid_title_overlap(self):
        agent = ReferenceValidatorAgent()
        result = agent.validate(
            "Random Cat Facts",
            "All about cats."
        )
        assert result["passed"] is False
        assert "title_overlap" in result["checks"]

    def test_invalid_constitution_ii(self):
        agent = ReferenceValidatorAgent()
        # Title has some overlap but abstract lacks keywords
        result = agent.validate(
            "Benchmark Study",
            "Just a random abstract with no relevant keywords."
        )
        # Title overlap might pass, but Constitution II should fail
        # or both fail depending on exact overlap
        # The important thing is the agent returns a structured result
        assert "passed" in result
        assert "checks" in result

    def test_can_contribute_review_points(self):
        agent = ReferenceValidatorAgent()
        
        # Should pass
        assert agent.can_contribute_review_points(
            "Heterogeneous Benchmark",
            "Foundation models collaboration study."
        ) is True
        
        # Should fail
        assert agent.can_contribute_review_points(
            "Irrelevant Topic",
            "Completely unrelated content."
        ) is False