"""
Unit tests for the ReferenceValidatorAgent.
"""
import pytest
from src.validators.reference_validator import ReferenceValidatorAgent


class TestReferenceValidatorAgent:
    """Test suite for ReferenceValidatorAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ReferenceValidatorAgent()

    def test_init_default_threshold(self):
        """Test initialization with default threshold."""
        assert self.agent.title_token_overlap_threshold == 0.7

    def test_init_custom_threshold(self):
        """Test initialization with custom threshold."""
        custom_agent = ReferenceValidatorAgent(threshold=0.5)
        assert custom_agent.title_token_overlap_threshold == 0.5

    def test_tokenize_title_basic(self):
        """Test basic tokenization."""
        tokens = self.agent._tokenize_title("Hello World Test")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert len(tokens) == 3

    def test_tokenize_title_empty(self):
        """Test tokenization of empty string."""
        tokens = self.agent._tokenize_title("")
        assert tokens == set()

    def test_tokenize_title_case_insensitive(self):
        """Test that tokenization is case insensitive."""
        tokens = self.agent._tokenize_title("HELLO World")
        assert "hello" in tokens
        assert "world" in tokens

    def test_compute_token_overlap_identical(self):
        """Test overlap of identical titles."""
        overlap = self.agent.compute_token_overlap("Test Title", "Test Title")
        assert overlap == 1.0

    def test_compute_token_overlap_different(self):
        """Test overlap of completely different titles."""
        overlap = self.agent.compute_token_overlap("Apple Orange", "Banana Grape")
        assert overlap == 0.0

    def test_compute_token_overlap_partial(self):
        """Test partial overlap."""
        overlap = self.agent.compute_token_overlap("A B C", "B C D")
        # Intersection: {B, C} (2), Union: {A, B, C, D} (4) -> 0.5
        assert overlap == 0.5

    def test_check_title_token_overlap_pass(self):
        """Test check that passes threshold."""
        # Threshold is 0.7 by default
        # "A B C D E" vs "A B C D F" -> overlap 4/5 = 0.8
        passes, score = self.agent.check_title_token_overlap(
            "A B C D E", "A B C D F"
        )
        assert passes is True
        assert score == 0.8

    def test_check_title_token_overlap_fail(self):
        """Test check that fails threshold."""
        # "A B" vs "C D" -> overlap 0/4 = 0.0
        passes, score = self.agent.check_title_token_overlap(
            "A B", "C D"
        )
        assert passes is False
        assert score == 0.0

    def test_validate_constitution_ii_compliance_valid(self):
        """Test validation of a compliant contribution."""
        contribution = {
            "title": "Test",
            "reference_title": "Test",
            "citations": ["ref1"],
            "data_sources": ["source1"],
            "results_type": "real_measurement"
        }
        is_compliant, violations = self.agent.validate_constitution_ii_compliance(contribution)
        assert is_compliant is True
        assert len(violations) == 0

    def test_validate_constitution_ii_compliance_no_citations(self):
        """Test validation failing due to missing citations."""
        contribution = {
            "title": "Test",
            "reference_title": "Test",
            "citations": [],
            "data_sources": ["source1"],
            "results_type": "real_measurement"
        }
        is_compliant, violations = self.agent.validate_constitution_ii_compliance(contribution)
        assert is_compliant is False
        assert any("No citations" in v for v in violations)

    def test_validate_constitution_ii_compliance_fabricated(self):
        """Test validation failing due to fabricated results."""
        contribution = {
            "title": "Test",
            "reference_title": "Test",
            "citations": ["ref1"],
            "data_sources": ["source1"],
            "results_type": "fabricated"
        }
        is_compliant, violations = self.agent.validate_constitution_ii_compliance(contribution)
        assert is_compliant is False
        assert any("fabricated" in v.lower() for v in violations)

    def test_validate_contribution_full_pass(self):
        """Test full validation pipeline passing."""
        contribution = {
            "title": "A B C D E",
            "reference_title": "A B C D F",
            "citations": ["ref1"],
            "data_sources": ["source1"],
            "results_type": "real_measurement"
        }
        result = self.agent.validate_contribution(contribution)
        assert result["is_valid"] is True
        assert result["can_contribute_points"] is True
        assert result["overlap_score"] == 0.8

    def test_validate_contribution_full_fail_overlap(self):
        """Test full validation pipeline failing on overlap."""
        contribution = {
            "title": "A B",
            "reference_title": "C D",
            "citations": ["ref1"],
            "data_sources": ["source1"],
            "results_type": "real_measurement"
        }
        result = self.agent.validate_contribution(contribution)
        assert result["is_valid"] is True
        assert result["can_contribute_points"] is False
        assert result["overlap_score"] == 0.0

    def test_validate_contribution_full_fail_fabrication(self):
        """Test full validation pipeline failing on fabrication."""
        contribution = {
            "title": "A B C D E",
            "reference_title": "A B C D F",
            "citations": ["ref1"],
            "data_sources": ["source1"],
            "results_type": "fabricated"
        }
        result = self.agent.validate_contribution(contribution)
        assert result["is_valid"] is False
        assert result["can_contribute_points"] is False
        assert len(result["violations"]) > 0
