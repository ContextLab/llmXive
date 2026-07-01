"""
Unit tests for the Reference Validator Agent.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.validators.reference_validator import (
    tokenize_title,
    compute_title_token_overlap,
    validate_reference_title_overlap,
    check_constitution_ii_compliance,
    ReferenceValidatorAgent
)


class TestTokenizeTitle:
    def test_basic_tokenization(self):
        title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"
        tokens = tokenize_title(title)
        assert "heterogeneous" in tokens
        assert "scientific" in tokens
        assert "foundation" in tokens
        assert "model" in tokens
        assert "collaboration" in tokens
        assert "benchmark" in tokens
        assert "the" not in tokens  # Stop word
        assert "and" not in tokens  # Stop word

    def test_empty_title(self):
        assert tokenize_title("") == []
        assert tokenize_title(None) == []

    def test_punctuation_handling(self):
        title = "Hello, World! How are you?"
        tokens = tokenize_title(title)
        assert "hello" in tokens
        assert "world" in tokens
        assert "how" not in tokens  # Stop word
        assert "are" not in tokens  # Stop word

    def test_single_word(self):
        assert len(tokenize_title("Test")) == 1
        assert tokenize_title("A") == []  # Too short


class TestComputeTitleTokenOverlap:
    def test_identical_titles(self):
        title = "Same Title Here"
        overlap = compute_title_token_overlap(title, title)
        assert overlap == 1.0

    def test_completely_different(self):
        title_a = "Completely Different Words"
        title_b = "Nothing In Common Here"
        overlap = compute_title_token_overlap(title_a, title_b)
        assert overlap == 0.0

    def test_partial_overlap(self):
        title_a = "Machine Learning for Science"
        title_b = "Deep Learning for Research"
        overlap = compute_title_token_overlap(title_a, title_b)
        # Expected: "learning" and "for" are common.
        # Tokens A: machine, learning, science
        # Tokens B: deep, learning, research
        # Intersection: {learning} -> 1
        # Union: {machine, learning, science, deep, research} -> 5
        # Overlap: 1/5 = 0.2
        assert 0.1 < overlap < 0.3

    def test_short_titles(self):
        # Titles with only one meaningful token should return 0.0
        overlap = compute_title_token_overlap("Test", "Test")
        assert overlap == 0.0


class TestValidateReferenceTitleOverlap:
    def test_pass_threshold(self):
        candidate = "Heterogeneous Scientific Model"
        references = ["Heterogeneous Scientific Foundation Model"]
        is_valid, details = validate_reference_title_overlap(candidate, references, threshold=0.5)
        # Should pass because overlap is high
        assert is_valid is True
        assert details["best_overlap"] >= 0.5

    def test_fail_threshold(self):
        candidate = "Completely Different Topic"
        references = ["Heterogeneous Scientific Foundation Model"]
        is_valid, details = validate_reference_title_overlap(candidate, references, threshold=0.5)
        assert is_valid is False
        assert details["best_overlap"] < 0.5

    def test_no_references(self):
        candidate = "Some Title"
        is_valid, details = validate_reference_title_overlap(candidate, [], threshold=0.5)
        assert is_valid is False
        assert "error" in details

    def test_invalid_candidate(self):
        is_valid, details = validate_reference_title_overlap("", ["Ref"], threshold=0.5)
        assert is_valid is False
        assert "error" in details


class TestCheckConstitutionIICompliance:
    def test_compliant_with_no_refs(self):
        review = {"title": "New Idea"}
        assert check_constitution_ii_compliance(review, reference_db_path=None) is True

    def test_compliant_with_distinct_title(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "references": [
                    {"title": "Existing Reference One"},
                    {"title": "Existing Reference Two"}
                ]
            }, f)
            temp_path = Path(f.name)

        try:
            review = {"title": "Completely Different New Idea"}
            result = check_constitution_ii_compliance(review, temp_path, threshold=0.7)
            # Should be compliant (not similar)
            assert result is True
        finally:
            temp_path.unlink()

    def test_non_compliant_with_similar_title(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "references": [
                    {"title": "Heterogeneous Scientific Foundation Model"}
                ]
            }, f)
            temp_path = Path(f.name)

        try:
            review = {"title": "Heterogeneous Scientific Model"}
            result = check_constitution_ii_compliance(review, temp_path, threshold=0.5)
            # Should be non-compliant (too similar)
            assert result is False
        finally:
            temp_path.unlink()


class TestReferenceValidatorAgent:
    def test_initialization(self):
        agent = ReferenceValidatorAgent()
        assert agent.get_reference_count() == 0

    def test_add_reference(self):
        agent = ReferenceValidatorAgent()
        agent.add_reference("Test Title")
        assert agent.get_reference_count() == 1

    def test_validate_contribution_compliant(self):
        agent = ReferenceValidatorAgent()
        agent.add_reference("Existing Reference")
        review = {"title": "Completely Different Title"}
        compliant, details = agent.validate_contribution(review, threshold=0.5)
        assert compliant is True

    def test_validate_contribution_non_compliant(self):
        agent = ReferenceValidatorAgent()
        agent.add_reference("Heterogeneous Scientific Model")
        review = {"title": "Heterogeneous Scientific Foundation Model"}
        compliant, details = agent.validate_contribution(review, threshold=0.5)
        assert compliant is False

    def test_reload_references(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({
                "references": [{"title": "Ref1"}, {"title": "Ref2"}]
            }, f)
            temp_path = Path(f.name)

        try:
            agent = ReferenceValidatorAgent(reference_db_path=temp_path)
            assert agent.get_reference_count() == 2
            agent.reload_references()
            assert agent.get_reference_count() == 2
        finally:
            temp_path.unlink()
