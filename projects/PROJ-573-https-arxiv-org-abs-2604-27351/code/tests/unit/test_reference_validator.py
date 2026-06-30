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
    def test_simple_tokenization(self):
        title = "Hello World"
        tokens = tokenize_title(title)
        assert tokens == ["hello", "world"]

    def test_punctuation_removal(self):
        title = "Hello, World! How are you?"
        tokens = tokenize_title(title)
        assert "hello" in tokens
        assert "world" in tokens
        assert "how" in tokens
        assert "are" in tokens
        assert "you" in tokens
        assert "," not in tokens
        assert "!" not in tokens
        assert "?" not in tokens

    def test_empty_title(self):
        assert tokenize_title("") == []
        assert tokenize_title(None) == []

    def test_single_char_filtering(self):
        title = "A B C"
        tokens = tokenize_title(title)
        # Single chars should be filtered
        assert len(tokens) == 0

    def test_case_insensitivity(self):
        title = "HeLLo WoRLd"
        tokens = tokenize_title(title)
        assert tokens == ["hello", "world"]


class TestComputeTitleTokenOverlap:
    def test_identical_titles(self):
        title1 = "Scientific Benchmark Model"
        title2 = "Scientific Benchmark Model"
        overlap = compute_title_token_overlap(title1, title2)
        assert overlap == 1.0

    def test_no_overlap(self):
        title1 = "Cat Dog Bird"
        title2 = "Car Bus Train"
        overlap = compute_title_token_overlap(title1, title2)
        assert overlap == 0.0

    def test_partial_overlap(self):
        title1 = "Scientific Model Benchmark"
        title2 = "Scientific Data Analysis"
        # Common: "scientific" -> 1 / (3 + 3 - 1) = 1/5 = 0.2
        overlap = compute_title_token_overlap(title1, title2)
        assert overlap == 0.2

    def test_empty_inputs(self):
        assert compute_title_token_overlap("", "") == 0.0
        assert compute_title_token_overlap("A", "") == 0.0
        assert compute_title_token_overlap("", "B") == 0.0


class TestValidateReferenceTitleOverlap:
    def test_valid_overlap(self):
        candidate = "Scientific Benchmark Model"
        references = [
            "Scientific Benchmark Analysis",
            "Completely Different Topic"
        ]
        is_valid, score, closest = validate_reference_title_overlap(candidate, references)
        assert is_valid is True
        assert score > 0.0
        assert closest == "Scientific Benchmark Analysis"

    def test_invalid_overlap(self):
        candidate = "Random Unrelated Title"
        references = [
            "Scientific Benchmark Model",
            "Tabular Data Analysis"
        ]
        is_valid, score, closest = validate_reference_title_overlap(candidate, references)
        assert is_valid is False
        assert score < 0.7

    def test_empty_references(self):
        is_valid, score, closest = validate_reference_title_overlap("Any Title", [])
        assert is_valid is False
        assert score == 0.0
        assert closest is None


class TestCheckConstitutionIICompliance:
    def test_compliant_context(self):
        context = {
            "title": "Scientific Benchmark Model",
            "reference_titles": ["Scientific Benchmark Analysis"],
            "review_points": 5
        }
        assert check_constitution_ii_compliance(context) is True

    def test_non_compliant_context(self):
        context = {
            "title": "Random Unrelated Title",
            "reference_titles": ["Scientific Benchmark Model"],
            "review_points": 5
        }
        assert check_constitution_ii_compliance(context) is False

    def test_zero_points_bypass(self):
        context = {
            "title": "Random Unrelated Title",
            "reference_titles": ["Scientific Benchmark Model"],
            "review_points": 0
        }
        # No points to contribute, so it passes
        assert check_constitution_ii_compliance(context) is True

    def test_missing_title_fails(self):
        context = {
            "title": "",
            "reference_titles": ["Scientific Benchmark Model"],
            "review_points": 5
        }
        assert check_constitution_ii_compliance(context) is False


class TestReferenceValidatorAgent:
    @pytest.fixture
    def agent(self):
        return ReferenceValidatorAgent([
            "Scientific Benchmark Model",
            "Tabular Data Analysis"
        ])

    def test_valid_contribution(self, agent):
        result = agent.validate_and_contribute(
            candidate_title="Scientific Benchmark Analysis",
            review_points=10
        )
        assert result["allowed"] is True
        assert result["points_contributed"] == 10
        assert result["overlap_score"] > 0.0

    def test_invalid_contribution_blocked(self, agent):
        result = agent.validate_and_contribute(
            candidate_title="Completely Random Title",
            review_points=10
        )
        assert result["allowed"] is False
        assert result["points_contributed"] == 0
        assert "blocked" in result["reason"].lower()

    def test_zero_points_contribution(self, agent):
        result = agent.validate_and_contribute(
            candidate_title="Completely Random Title",
            review_points=0
        )
        assert result["allowed"] is True
        assert result["points_contributed"] == 0

    def test_get_reference_titles(self, agent):
        titles = agent.get_reference_titles()
        assert len(titles) == 2
        assert "Scientific Benchmark Model" in titles