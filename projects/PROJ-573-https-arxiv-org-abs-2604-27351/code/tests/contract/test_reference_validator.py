import pytest
import json
import tempfile
from pathlib import Path
from src.validators.reference_validator import ReferenceValidatorAgent, compute_title_token_overlap

class TestReferenceValidatorSchema:
    """Contract tests for ReferenceValidatorAgent functionality."""
    
    def test_compute_title_token_overlap_identical(self):
        """Test overlap of identical titles."""
        title = "Heterogeneous Scientific Foundation Model"
        score = compute_title_token_overlap(title, title)
        assert score == 1.0
    
    def test_compute_title_token_overlap_completely_different(self):
        """Test overlap of completely different titles."""
        title1 = "Deep Learning for Image Recognition"
        title2 = "Quantum Computing Algorithms"
        score = compute_title_token_overlap(title1, title2)
        assert score == 0.0
    
    def test_compute_title_token_overlap_partial(self):
        """Test overlap of partially similar titles."""
        title1 = "Scientific Foundation Models"
        title2 = "Foundation Models for Science"
        score = compute_title_token_overlap(title1, title2)
        assert 0.0 < score < 1.0
    
    def test_compute_title_token_overlap_empty(self):
        """Test overlap with empty strings."""
        assert compute_title_token_overlap("", "") == 0.0
        assert compute_title_token_overlap("title", "") == 0.0
        assert compute_title_token_overlap("", "title") == 0.0
    
    def test_reference_validator_agent_initialization(self):
        """Test agent initialization with custom threshold."""
        agent = ReferenceValidatorAgent(overlap_threshold=0.5)
        assert agent.overlap_threshold == 0.5
    
    def test_validate_claim_reference_pass(self):
        """Test validation that passes the threshold."""
        agent = ReferenceValidatorAgent(overlap_threshold=0.5)
        result = agent.validate_claim_reference(
            "Scientific Models",
            "Scientific Foundation Models"
        )
        assert result["is_valid"] is True
        assert result["overlap_score"] >= 0.5
    
    def test_validate_claim_reference_fail(self):
        """Test validation that fails the threshold."""
        agent = ReferenceValidatorAgent(overlap_threshold=0.9)
        result = agent.validate_claim_reference(
            "Image Recognition",
            "Quantum Computing"
        )
        assert result["is_valid"] is False
        assert result["overlap_score"] < 0.9
    
    def test_gate_contribution_compliant(self):
        """Test gate with compliant review data."""
        agent = ReferenceValidatorAgent()
        review_data = {
            "peer_review_compliance": True,
            "citation_accuracy": True,
            "claim_verification": True,
            "claims": []
        }
        can_contribute, reason = agent.gate_contribution(review_data)
        assert can_contribute is True
        assert "approved" in reason.lower()
    
    def test_gate_contribution_non_compliant(self):
        """Test gate with non-compliant review data."""
        agent = ReferenceValidatorAgent()
        review_data = {
            "peer_review_compliance": False,
            "citation_accuracy": True,
            "claim_verification": True,
            "claims": []
        }
        can_contribute, reason = agent.gate_contribution(review_data)
        assert can_contribute is False
        assert "compliance failed" in reason.lower()
    
    def test_get_validation_summary(self):
        """Test validation summary generation."""
        agent = ReferenceValidatorAgent()
        agent.validate_claim_reference("Test", "Test")
        agent.validate_claim_reference("A", "B")
        
        summary = agent.get_validation_summary()
        assert summary["total_validations"] == 2
        assert summary["passed_count"] == 1
        assert summary["failed_count"] == 1
        assert summary["threshold_used"] == 0.7

if __name__ == "__main__":
    pytest.main([__file__, "-v"])