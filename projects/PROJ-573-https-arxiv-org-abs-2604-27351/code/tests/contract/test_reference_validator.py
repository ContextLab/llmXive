"""
Contract tests for the ReferenceValidatorAgent.
"""
import pytest
import json
import tempfile
from pathlib import Path

from src.validators.reference_validator import ReferenceValidatorAgent, compute_title_token_overlap


class TestReferenceValidatorSchema:
    """Contract tests ensuring ReferenceValidatorAgent meets specification."""

    def test_init_default(self):
        """Test initialization with default configuration."""
        agent = ReferenceValidatorAgent()
        assert agent.min_overlap_threshold == 0.7
        assert agent.config == {}

    def test_init_custom_threshold(self):
        """Test initialization with custom threshold."""
        agent = ReferenceValidatorAgent(config={"min_overlap_threshold": 0.5})
        assert agent.min_overlap_threshold == 0.5

    def test_title_token_overlap_exact(self):
        """Test overlap calculation for identical titles."""
        score = compute_title_token_overlap("Test Title", "Test Title")
        assert score == 1.0

    def test_title_token_overlap_partial(self):
        """Test overlap calculation for partially matching titles."""
        score = compute_title_token_overlap("Heterogeneous Model", "Model Heterogeneous")
        # Both have 2 tokens, intersection is 2, union is 2 -> 1.0
        assert score == 1.0

    def test_title_token_overlap_none(self):
        """Test overlap calculation for empty titles."""
        score = compute_title_token_overlap("", "Title")
        assert score == 0.0
        score = compute_title_token_overlap("Title", "")
        assert score == 0.0

    def test_validate_title_match_pass(self):
        """Test validation when overlap is above threshold."""
        agent = ReferenceValidatorAgent()
        is_valid, score = agent.validate_title_match("Good Title", "Good Title")
        assert is_valid is True
        assert score == 1.0

    def test_validate_title_match_fail(self):
        """Test validation when overlap is below threshold."""
        agent = ReferenceValidatorAgent()
        is_valid, score = agent.validate_title_match("Different", "Good Title")
        assert is_valid is False
        assert score < 0.7

    def test_constitution_ii_compliance_pass(self):
        """Test full compliance check with valid data."""
        agent = ReferenceValidatorAgent()
        data = {
            "title": "Test Title",
            "reference_title": "Test Title",
            "source": "arxiv.org",
            "citation": "1234.5678"
        }
        is_compliant, missing = agent.check_constitution_ii_compliance(data)
        assert is_compliant is True
        assert len(missing) == 0

    def test_constitution_ii_compliance_fail_title(self):
        """Test compliance check failing on title overlap."""
        agent = ReferenceValidatorAgent()
        data = {
            "title": "Different Title",
            "reference_title": "Original Title",
            "source": "arxiv.org",
            "citation": "1234.5678"
        }
        is_compliant, missing = agent.check_constitution_ii_compliance(data)
        assert is_compliant is False
        assert "title_token_overlap" in missing

    def test_constitution_ii_compliance_fail_source(self):
        """Test compliance check failing on missing source."""
        agent = ReferenceValidatorAgent()
        data = {
            "title": "Test Title",
            "reference_title": "Test Title",
            "source": "",
            "citation": "1234.5678"
        }
        is_compliant, missing = agent.check_constitution_ii_compliance(data)
        assert is_compliant is False
        assert "source_verification" in missing

    def test_constitution_ii_compliance_fail_citation(self):
        """Test compliance check failing on missing citation."""
        agent = ReferenceValidatorAgent()
        data = {
            "title": "Test Title",
            "reference_title": "Test Title",
            "source": "arxiv.org",
            "citation": ""
        }
        is_compliant, missing = agent.check_constitution_ii_compliance(data)
        assert is_compliant is False
        assert "citation_format" in missing

    def test_evaluate_contribution_complete(self):
        """Test the full evaluate_contribution method."""
        agent = ReferenceValidatorAgent()
        data = {
            "title": "Test Title",
            "reference_title": "Test Title",
            "source": "arxiv.org",
            "citation": "1234.5678"
        }
        result = agent.evaluate_contribution(data)
        assert result["passed"] is True
        assert result["missing_requirements"] == []
        assert result["score"] == 1.0
        assert "approved" in result["message"]

    def test_evaluate_contribution_blocked(self):
        """Test the full evaluate_contribution method for blocked case."""
        agent = ReferenceValidatorAgent()
        data = {
            "title": "Bad Title",
            "reference_title": "Good Title",
            "source": "arxiv.org",
            "citation": "1234.5678"
        }
        result = agent.evaluate_contribution(data)
        assert result["passed"] is False
        assert "title_token_overlap" in result["missing_requirements"]
        assert "blocked" in result["message"]