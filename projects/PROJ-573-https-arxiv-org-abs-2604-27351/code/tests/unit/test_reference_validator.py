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
    """Tests for the tokenize_title function."""
    
    def test_basic_tokenization(self):
        """Test basic title tokenization."""
        title = "Heterogeneous Scientific Foundation Model"
        tokens = tokenize_title(title)
        assert "heterogeneous" in tokens
        assert "scientific" in tokens
        assert "foundation" in tokens
        assert "model" in tokens
    
    def test_empty_string(self):
        """Test tokenization of empty string."""
        assert tokenize_title("") == []
    
    def test_special_characters(self):
        """Test handling of special characters."""
        title = "Model v2.0: A New Approach!"
        tokens = tokenize_title(title)
        assert "model" in tokens
        assert "v20" in tokens  # Version number should be tokenized
        assert "a" in tokens
        assert "new" in tokens
        assert "approach" in tokens
    
    def test_single_char_filtering(self):
        """Test that single characters are filtered out."""
        title = "A B C Test"
        tokens = tokenize_title(title)
        assert "a" not in tokens
        assert "b" not in tokens
        assert "c" not in tokens
        assert "test" in tokens


class TestComputeTitleTokenOverlap:
    """Tests for the compute_title_token_overlap function."""
    
    def test_identical_titles(self):
        """Test overlap of identical titles."""
        title = "Heterogeneous Scientific Foundation Model"
        overlap = compute_title_token_overlap(title, title)
        assert overlap == 1.0
    
    def test_completely_different_titles(self):
        """Test overlap of completely different titles."""
        title_a = "Heterogeneous Scientific Foundation Model"
        title_b = "Completely Unrelated Research Topic"
        overlap = compute_title_token_overlap(title_a, title_b)
        assert overlap == 0.0
    
    def test_partial_overlap(self):
        """Test overlap with partial common tokens."""
        title_a = "Heterogeneous Scientific Foundation Model"
        title_b = "Heterogeneous Approach to Foundation Models"
        overlap = compute_title_token_overlap(title_a, title_b)
        # Common tokens: heterogeneous, foundation, model(s)
        assert 0.0 < overlap < 1.0
    
    def test_empty_titles(self):
        """Test overlap with empty titles."""
        assert compute_title_token_overlap("", "") == 0.0
        assert compute_title_token_overlap("Title A", "") == 0.0
        assert compute_title_token_overlap("", "Title B") == 0.0


class TestValidateReferenceTitleOverlap:
    """Tests for the validate_reference_title_overlap function."""
    
    def test_above_threshold(self):
        """Test validation when overlap is above threshold."""
        title_a = "Heterogeneous Scientific Foundation Model"
        title_b = "Heterogeneous Scientific Foundation Model"
        is_valid, score = validate_reference_title_overlap(
            title_a, title_b, threshold=0.7
        )
        assert is_valid is True
        assert score == 1.0
    
    def test_below_threshold(self):
        """Test validation when overlap is below threshold."""
        title_a = "Heterogeneous Scientific Foundation Model"
        title_b = "Completely Unrelated Research Topic"
        is_valid, score = validate_reference_title_overlap(
            title_a, title_b, threshold=0.7
        )
        assert is_valid is False
        assert score == 0.0
    
    def test_custom_threshold(self):
        """Test with custom threshold."""
        title_a = "Heterogeneous Scientific Foundation Model"
        title_b = "Heterogeneous Approach to Foundation Models"
        is_valid, score = validate_reference_title_overlap(
            title_a, title_b, threshold=0.9
        )
        assert is_valid is False  # Likely below 0.9
        assert score < 0.9


class TestCheckConstitutionIICompliance:
    """Tests for the check_constitution_ii_compliance function."""
    
    def test_full_compliance(self):
        """Test review with all requirements met."""
        review = {
            "claim_title": "Test Claim",
            "reference_title": "Test Claim",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": False
        }
        is_compliant, violations = check_constitution_ii_compliance(review)
        assert is_compliant is True
        assert len(violations) == 0
    
    def test_missing_claim_title(self):
        """Test review with missing claim title."""
        review = {
            "claim_title": "",
            "reference_title": "Test Reference",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": False
        }
        is_compliant, violations = check_constitution_ii_compliance(review)
        assert is_compliant is False
        assert any("Missing claim title" in v for v in violations)
    
    def test_missing_reference_title(self):
        """Test review with missing reference title."""
        review = {
            "claim_title": "Test Claim",
            "reference_title": "",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": False
        }
        is_compliant, violations = check_constitution_ii_compliance(review)
        assert is_compliant is False
        assert any("Missing reference title" in v for v in violations)
    
    def test_no_evidence(self):
        """Test review with no evidence provided."""
        review = {
            "claim_title": "Test Claim",
            "reference_title": "Test Reference",
            "evidence_provided": False,
            "methodology_documented": True,
            "data_fabricated": False
        }
        is_compliant, violations = check_constitution_ii_compliance(review)
        assert is_compliant is False
        assert any("No evidence provided" in v for v in violations)
    
    def test_fabricated_data(self):
        """Test review with fabricated data."""
        review = {
            "claim_title": "Test Claim",
            "reference_title": "Test Reference",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": True
        }
        is_compliant, violations = check_constitution_ii_compliance(review)
        assert is_compliant is False
        assert any("Fabricated data" in v for v in violations)


class TestReferenceValidatorAgent:
    """Tests for the ReferenceValidatorAgent class."""
    
    def test_init(self):
        """Test agent initialization."""
        agent = ReferenceValidatorAgent(
            overlap_threshold=0.8,
            gating_enabled=False
        )
        assert agent.overlap_threshold == 0.8
        assert agent.gating_enabled is False
        assert len(agent.validation_log) == 0
    
    def test_validate_valid_review(self):
        """Test validation of a compliant review."""
        agent = ReferenceValidatorAgent()
        review = {
            "claim_title": "Test Claim",
            "reference_title": "Test Claim",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": False
        }
        result = agent.validate_review(review)
        
        assert result["is_valid"] is True
        assert result["can_contribute_points"] is True
        assert result["constitution_ii_compliant"] is True
        assert len(result["violations"]) == 0
        assert len(agent.validation_log) == 1
    
    def test_validate_invalid_overlap(self):
        """Test validation of a review with low title overlap."""
        agent = ReferenceValidatorAgent()
        review = {
            "claim_title": "Heterogeneous Scientific Foundation Model",
            "reference_title": "Completely Unrelated Research",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": False
        }
        result = agent.validate_review(review)
        
        assert result["is_valid"] is False
        assert result["can_contribute_points"] is False
        assert result["title_overlap_valid"] is False
    
    def test_validate_constitution_violation(self):
        """Test validation of a review with Constitution II violation."""
        agent = ReferenceValidatorAgent()
        review = {
            "claim_title": "Test Claim",
            "reference_title": "Test Claim",
            "evidence_provided": False,
            "methodology_documented": True,
            "data_fabricated": False
        }
        result = agent.validate_review(review)
        
        assert result["is_valid"] is False
        assert result["can_contribute_points"] is False
        assert result["constitution_ii_compliant"] is False
        assert any("No evidence provided" in v for v in result["violations"])
    
    def test_gating_disabled(self):
        """Test that gating can be disabled."""
        agent = ReferenceValidatorAgent(gating_enabled=False)
        review = {
            "claim_title": "Test Claim",
            "reference_title": "Completely Unrelated",
            "evidence_provided": True,
            "methodology_documented": True,
            "data_fabricated": False
        }
        result = agent.validate_review(review)
        
        # Should still be invalid, but the log message about blocking won't appear
        assert result["is_valid"] is False
        assert result["can_contribute_points"] is False
    
    def test_validation_stats(self):
        """Test validation statistics calculation."""
        agent = ReferenceValidatorAgent()
        
        # Add some valid reviews
        for i in range(3):
            agent.validate_review({
                "claim_title": "Test Claim",
                "reference_title": "Test Claim",
                "evidence_provided": True,
                "methodology_documented": True,
                "data_fabricated": False
            })
        
        # Add some invalid reviews
        for i in range(2):
            agent.validate_review({
                "claim_title": "Test Claim",
                "reference_title": "Unrelated",
                "evidence_provided": True,
                "methodology_documented": True,
                "data_fabricated": False
            })
        
        stats = agent.get_validation_stats()
        
        assert stats["total_validations"] == 5
        assert stats["passed"] == 3
        assert stats["failed"] == 2
        assert stats["pass_rate"] == 0.6
    
    def test_empty_stats(self):
        """Test statistics when no validations have occurred."""
        agent = ReferenceValidatorAgent()
        stats = agent.get_validation_stats()
        
        assert stats["total_validations"] == 0
        assert stats["passed"] == 0
        assert stats["failed"] == 0
        assert stats["pass_rate"] == 0.0