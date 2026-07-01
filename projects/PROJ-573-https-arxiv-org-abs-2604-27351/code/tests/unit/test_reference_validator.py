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
    def test_simple_title(self):
        title = "Hello World"
        tokens = tokenize_title(title)
        assert "hello" in tokens
        assert "world" in tokens

    def test_empty_title(self):
        assert tokenize_title("") == []
        assert tokenize_title(None) == []

    def test_special_characters(self):
        title = "A Study on 123-456: The Results!"
        tokens = tokenize_title(title)
        assert "study" in tokens
        assert "123" in tokens
        assert "456" in tokens
        assert "results" in tokens

    def test_case_insensitivity(self):
        title = "HeLLo WoRLd"
        tokens = tokenize_title(title)
        assert "hello" in tokens
        assert "world" in tokens

class TestComputeTitleTokenOverlap:
    def test_identical_titles(self):
        title = "Same Title"
        assert compute_title_token_overlap(title, title) == 1.0

    def test_no_overlap(self):
        title_a = "Completely Different"
        title_b = "Nothing In Common"
        assert compute_title_token_overlap(title_a, title_b) == 0.0

    def test_partial_overlap(self):
        title_a = "Scientific Foundation Models"
        title_b = "Foundation Models for Science"
        overlap = compute_title_token_overlap(title_a, title_b)
        # Common: "foundation", "models", "science"/"scientific" (different)
        # tokens_a: scientific, foundation, models
        # tokens_b: foundation, models, science
        # intersection: foundation, models (2)
        # union: scientific, foundation, models, science (4)
        assert overlap == 0.5

    def test_empty_titles(self):
        assert compute_title_token_overlap("", "") == 0.0
        assert compute_title_token_overlap("Title", "") == 0.0

class TestValidateReferenceTitleOverlap:
    def test_pass_threshold(self):
        ref_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"
        target_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"
        is_valid, score = validate_reference_title_overlap(ref_title, target_title, threshold=0.7)
        assert is_valid is True
        assert score == 1.0

    def test_fail_threshold(self):
        ref_title = "Completely Unrelated Title"
        target_title = "Heterogeneous Scientific Foundation Model Collaboration Benchmark"
        is_valid, score = validate_reference_title_overlap(ref_title, target_title, threshold=0.7)
        assert is_valid is False
        assert score < 0.7

    def test_custom_threshold(self):
        ref_title = "Some Shared Words Here"
        target_title = "Some Words Different Here"
        # Common: "some", "words", "here" (3)
        # Union: "some", "shared", "words", "here", "different" (5)
        # Overlap = 0.6
        is_valid_high, _ = validate_reference_title_overlap(ref_title, target_title, threshold=0.7)
        is_valid_low, _ = validate_reference_title_overlap(ref_title, target_title, threshold=0.5)
        assert is_valid_high is False
        assert is_valid_low is True

class TestCheckConstitutionIICompliance:
    def test_valid_reference(self):
        ref = {
            "title": "Test Title",
            "abstract": "This is a sufficiently long abstract that meets the requirements.",
            "doi": "10.1234/test",
            "authors": ["Alice", "Bob"]
        }
        is_compliant, violations = check_constitution_ii_compliance(ref)
        assert is_compliant is True
        assert len(violations) == 0

    def test_missing_abstract(self):
        ref = {
            "title": "Test Title",
            "doi": "10.1234/test",
            "authors": ["Alice"]
        }
        is_compliant, violations = check_constitution_ii_compliance(ref)
        assert is_compliant is False
        assert any("abstract" in v for v in violations)

    def test_missing_doi_arxiv(self):
        ref = {
            "title": "Test Title",
            "abstract": "This is a sufficiently long abstract that meets the requirements.",
            "authors": ["Alice"]
        }
        is_compliant, violations = check_constitution_ii_compliance(ref)
        assert is_compliant is False
        assert any("DOI" in v or "arXiv" in v for v in violations)

    def test_too_many_authors(self):
        ref = {
            "title": "Test Title",
            "abstract": "This is a sufficiently long abstract that meets the requirements.",
            "doi": "10.1234/test",
            "authors": [f"Author{i}" for i in range(51)]
        }
        is_compliant, violations = check_constitution_ii_compliance(ref)
        assert is_compliant is False
        assert any("authors" in v for v in violations)

class TestReferenceValidatorAgent:
    @pytest.fixture
    def validator(self):
        return ReferenceValidatorAgent(target_title="Heterogeneous Scientific Foundation Model Collaboration Benchmark")

    def test_validate_valid_reference(self, validator):
        ref = {
            "id": "ref_001",
            "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
            "abstract": "This is a sufficiently long abstract that meets the requirements.",
            "doi": "10.1234/test",
            "authors": ["Alice", "Bob"]
        }
        result = validator.validate_reference(ref)
        assert result["should_contribute_points"] is True
        assert result["passed_title_overlap"] is True
        assert result["passed_constitution_ii"] is True

    def test_validate_invalid_overlap(self, validator):
        ref = {
            "id": "ref_002",
            "title": "Completely Unrelated Title About Cats",
            "abstract": "This is a sufficiently long abstract that meets the requirements.",
            "doi": "10.1234/test",
            "authors": ["Alice"]
        }
        result = validator.validate_reference(ref)
        assert result["should_contribute_points"] is False
        assert result["passed_title_overlap"] is False

    def test_validate_invalid_constitution(self, validator):
        ref = {
            "id": "ref_003",
            "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
            "abstract": "Short",
            "authors": ["Alice"]
        }
        result = validator.validate_reference(ref)
        assert result["should_contribute_points"] is False
        assert result["passed_title_overlap"] is True
        assert result["passed_constitution_ii"] is False

    def test_validate_batch(self, validator):
        refs = [
            {
                "id": "ref_001",
                "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
                "abstract": "This is a sufficiently long abstract that meets the requirements.",
                "doi": "10.1234/test",
                "authors": ["Alice"]
            },
            {
                "id": "ref_002",
                "title": "Completely Unrelated",
                "abstract": "This is a sufficiently long abstract that meets the requirements.",
                "doi": "10.1234/test",
                "authors": ["Alice"]
            }
        ]
        results = validator.validate_batch(refs)
        assert len(results) == 2
        assert results[0]["should_contribute_points"] is True
        assert results[1]["should_contribute_points"] is False

    def test_validation_summary(self, validator):
        refs = [
            {
                "id": "ref_001",
                "title": "Heterogeneous Scientific Foundation Model Collaboration Benchmark",
                "abstract": "This is a sufficiently long abstract that meets the requirements.",
                "doi": "10.1234/test",
                "authors": ["Alice"]
            },
            {
                "id": "ref_002",
                "title": "Completely Unrelated",
                "abstract": "This is a sufficiently long abstract that meets the requirements.",
                "doi": "10.1234/test",
                "authors": ["Alice"]
            }
        ]
        validator.validate_batch(refs)
        summary = validator.get_validation_summary()
        assert summary["total_validated"] == 2
        assert summary["passed"] == 1
        assert summary["failed_overlap"] == 1
        assert summary["failed_constitution"] == 0
        assert summary["contribution_rate"] == 0.5