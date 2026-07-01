"""
Contract tests for ReferenceValidatorAgent.

These tests verify that the Reference Validator Agent correctly implements
the Constitution II compliance gate and title-token-overlap logic.
"""
import pytest
from src.validators.reference_validator import ReferenceValidatorAgent


class TestReferenceValidatorSchema:
    """Contract tests for the Reference Validator Agent API."""

    @pytest.fixture
    def agent(self):
        """Create a fresh agent instance for each test."""
        return ReferenceValidatorAgent(threshold=0.7)

    def test_init(self):
        """Test that agent initializes with correct threshold."""
        agent = ReferenceValidatorAgent(threshold=0.5)
        assert agent.threshold == 0.5
        assert agent.get_review_points() == 0

    def test_tokenization(self, agent):
        """Test that title tokenization works correctly."""
        title = "Heterogeneous Scientific Foundation Model"
        tokens = agent.tokenize_title(title)
        assert "heterogeneous" in tokens
        assert "scientific" in tokens
        assert "foundation" in tokens
        assert "model" in tokens
        # Short words should be filtered
        assert "a" not in tokens

    def test_overlap_identical_titles(self, agent):
        """Test that identical titles yield 1.0 overlap."""
        title = "Exact Match Title"
        score = agent.compute_title_token_overlap(title, title)
        assert score == 1.0

    def test_overlap_completely_different(self, agent):
        """Test that completely different titles yield 0.0 overlap."""
        score = agent.compute_title_token_overlap("Apple Banana", "Carrot Date")
        assert score == 0.0

    def test_validate_reference_pass(self, agent):
        """Test validation passes when overlap >= threshold."""
        ref = {"title": "Heterogeneous Scientific Foundation Model"}
        target = "Heterogeneous Scientific Foundation Model Benchmark"
        
        is_valid, score, reason = agent.validate_reference(ref, target)
        
        assert is_valid is True
        assert score >= agent.threshold
        assert "PASS" in reason or "threshold" in reason

    def test_validate_reference_fail(self, agent):
        """Test validation fails when overlap < threshold."""
        ref = {"title": "Completely Unrelated Topic"}
        target = "Heterogeneous Scientific Foundation Model"
        
        is_valid, score, reason = agent.validate_reference(ref, target)
        
        assert is_valid is False
        assert score < agent.threshold

    def test_constitution_ii_gate_pass(self, agent):
        """Test that the blocking gate allows compliant references."""
        ref = {"title": "Heterogeneous Scientific Foundation Model"}
        target = "Heterogeneous Scientific Foundation Model Benchmark"
        
        is_compliant = agent.check_constitution_ii_compliance(ref, target)
        
        assert is_compliant is True

    def test_constitution_ii_gate_block(self, agent):
        """Test that the blocking gate blocks non-compliant references."""
        ref = {"title": "Completely Unrelated Topic"}
        target = "Heterogeneous Scientific Foundation Model"
        
        is_compliant = agent.check_constitution_ii_compliance(ref, target)
        
        assert is_compliant is False

    def test_contribute_points_on_pass(self, agent):
        """Test that points are awarded only when gate passes."""
        initial_points = agent.get_review_points()
        ref = {"title": "Heterogeneous Scientific Foundation Model"}
        target = "Heterogeneous Scientific Foundation Model Benchmark"
        
        points = agent.contribute_review_points(ref, target)
        
        assert points == 1
        assert agent.get_review_points() == initial_points + 1

    def test_contribute_points_on_fail(self, agent):
        """Test that points are NOT awarded when gate blocks."""
        initial_points = agent.get_review_points()
        ref = {"title": "Completely Unrelated Topic"}
        target = "Heterogeneous Scientific Foundation Model"
        
        points = agent.contribute_review_points(ref, target)
        
        assert points == 0
        assert agent.get_review_points() == initial_points

    def test_batch_validation(self, agent):
        """Test batch validation logic."""
        refs = [
            {"title": "Heterogeneous Scientific Foundation Model"},
            {"title": "Completely Unrelated Topic"}
        ]
        target = "Heterogeneous Scientific Foundation Model Benchmark"
        
        results = agent.validate_batch(refs, target)
        
        assert results["total_references"] == 2
        assert results["valid_count"] == 1
        assert results["invalid_count"] == 1
        assert len(results["details"]) == 2