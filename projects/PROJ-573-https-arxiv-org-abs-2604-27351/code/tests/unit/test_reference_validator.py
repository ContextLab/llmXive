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
    def test_simple_tokens(self):
        title = "Hello World"
        tokens = tokenize_title(title)
        assert tokens == {"hello", "world"}

    def test_punctuation_removal(self):
        title = "Hello, World! 123"
        tokens = tokenize_title(title)
        assert tokens == {"hello", "world", "123"}

    def test_empty_title(self):
        assert tokenize_title("") == set()
        assert tokenize_title(None) == set()

    def test_case_insensitivity(self):
        title = "Hello HELLO"
        tokens = tokenize_title(title)
        assert tokens == {"hello"}


class TestComputeTitleTokenOverlap:
    def test_identical_titles(self):
        score = compute_title_token_overlap("A B C", "A B C")
        assert score == 1.0

    def test_no_overlap(self):
        score = compute_title_token_overlap("A B", "C D")
        assert score == 0.0

    def test_partial_overlap(self):
        # |{A, B} ∩ {B, C}| / |{A, B, C}| = 1 / 3
        score = compute_title_token_overlap("A B", "B C")
        assert abs(score - 1/3) < 0.001

    def test_empty_titles(self):
        score = compute_title_token_overlap("", "")
        assert score == 0.0


class TestValidateReferenceTitleOverlap:
    def test_pass_threshold(self):
        # Overlap will be high
        valid, score = validate_reference_title_overlap("Test Title", "Test Title")
        assert valid is True
        assert score == 1.0

    def test_fail_threshold(self):
        # Completely different
        valid, score = validate_reference_title_overlap("Completely Different", "Totally Unrelated")
        assert valid is False


class TestCheckConstitutionIICompliance:
    def test_all_claims_present(self):
        required = {"claim:c_5cb9c0de", "claim:c_55db4237", "claim:c_101df1fb"}
        metadata = {"cited_claims": list(required)}
        compliant, missing = check_constitution_ii_compliance(metadata)
        assert compliant is True
        assert missing == []

    def test_missing_claims(self):
        metadata = {"cited_claims": ["claim:c_123"]}
        compliant, missing = check_constitution_ii_compliance(metadata)
        assert compliant is False
        assert len(missing) == 3

    def test_empty_metadata(self):
        compliant, missing = check_constitution_ii_compliance({})
        assert compliant is False


class TestReferenceValidatorAgent:
    @pytest.fixture
    def agent(self):
        refs = {
            "T1": "Perfect Match Title",
            "T2": "Another Title"
        }
        return ReferenceValidatorAgent(reference_titles_map=refs)

    def test_init(self, agent):
        assert agent.get_review_points() == 0

    def test_validate_success(self, agent):
        required_claims = {"claim:c_5cb9c0de", "claim:c_55db4237", "claim:c_101df1fb"}
        result = agent.validate_and_approve(
            task_id="T1",
            candidate_title="Perfect Match Title",
            research_metadata={"cited_claims": list(required_claims)}
        )
        assert result is True
        assert agent.get_review_points() == 1

    def test_validate_fail_overlap(self, agent):
        required_claims = {"claim:c_5cb9c0de", "claim:c_55db4237", "claim:c_101df1fb"}
        result = agent.validate_and_approve(
            task_id="T1",
            candidate_title="Totally Wrong Title",
            research_metadata={"cited_claims": list(required_claims)}
        )
        assert result is False
        assert agent.get_review_points() == 0

    def test_validate_fail_constitution(self, agent):
        result = agent.validate_and_approve(
            task_id="T1",
            candidate_title="Perfect Match Title",
            research_metadata={"cited_claims": []}
        )
        assert result is False
        assert agent.get_review_points() == 0

    def test_unknown_task_id(self, agent):
        # Should pass overlap check if reference is missing, but fail constitution
        result = agent.validate_and_approve(
            task_id="UNKNOWN",
            candidate_title="Any Title",
            research_metadata={"cited_claims": []}
        )
        assert result is False

    def test_unknown_task_id_compliant(self, agent):
        required_claims = {"claim:c_5cb9c0de", "claim:c_55db4237", "claim:c_101df1fb"}
        result = agent.validate_and_approve(
            task_id="UNKNOWN",
            candidate_title="Any Title",
            research_metadata={"cited_claims": list(required_claims)}
        )
        assert result is True
        assert agent.get_review_points() == 1
