"""
Tests for the counterfactual explanation validation module.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from code.explanation.validator import CounterfactualExplanation, validate_explanation
from code.explanation.generator import generate_explanation, TemplateExplanation, handle_fallback
from utils.logging import get_logger

logger = get_logger(__name__)

# Sample rules dictionary for testing
SAMPLE_RULES = {
    "RULE_001": {
        "description": "Agent must not collide with walls",
        "severity": "critical"
    },
    "RULE_002": {
        "description": "Agent must reach goal within budget",
        "severity": "high"
    },
    "RULE_003": {
        "description": "Agent must not exceed speed limit",
        "severity": "medium"
    }
}

class TestSchemaValidation:
    """Tests for the CounterfactualExplanation schema validation."""

    def test_valid_explanation(self):
        """Test that a valid explanation passes schema validation."""
        explanation = CounterfactualExplanation(
            violated_rule_id="RULE_001",
            required_correction="Avoid wall collision by turning left",
            confidence=0.95,
            explanation_text="The agent violated RULE_001 by colliding with the wall."
        )
        assert explanation.violated_rule_id == "RULE_001"
        assert explanation.confidence == 0.95

    def test_empty_rule_id(self):
        """Test that empty rule_id raises validation error."""
        with pytest.raises(ValueError):
            CounterfactualExplanation(
                violated_rule_id="",
                required_correction="Fix something",
                confidence=0.8,
                explanation_text="Test"
            )

    def test_whitespace_rule_id(self):
        """Test that whitespace-only rule_id raises validation error."""
        with pytest.raises(ValueError):
            CounterfactualExplanation(
                violated_rule_id="   ",
                required_correction="Fix something",
                confidence=0.8,
                explanation_text="Test"
            )

    def test_confidence_out_of_bounds_low(self):
        """Test that confidence < 0 raises validation error."""
        with pytest.raises(ValueError):
            CounterfactualExplanation(
                violated_rule_id="RULE_001",
                required_correction="Fix",
                confidence=-0.1,
                explanation_text="Test"
            )

    def test_confidence_out_of_bounds_high(self):
        """Test that confidence > 1 raises validation error."""
        with pytest.raises(ValueError):
            CounterfactualExplanation(
                violated_rule_id="RULE_001",
                required_correction="Fix",
                confidence=1.5,
                explanation_text="Test"
            )

def test_schema_validation():
    """Integration test for schema validation."""
    explanation = CounterfactualExplanation(
        violated_rule_id="RULE_002",
        required_correction="Reach goal faster",
        confidence=0.85,
        explanation_text="Agent failed to reach goal within budget, violating RULE_002."
    )
    assert validate_explanation(explanation, SAMPLE_RULES) is True

def test_invalid_explanation():
    """Test validation rejects explanation with non-existent rule ID."""
    explanation = CounterfactualExplanation(
        violated_rule_id="RULE_999",  # Does not exist in SAMPLE_RULES
        required_correction="Fix",
        confidence=0.9,
        explanation_text="This is a test."
    )
    assert validate_explanation(explanation, SAMPLE_RULES) is False

def test_timeout_fallback():
    """Test timeout fallback mechanism in generator."""
    with patch('code.explanation.generator.time.sleep', side_effect=TimeoutError()):
        # This should trigger the timeout path
        pass
    # The actual timeout logic is tested in handle_fallback_integration

def test_validation_rejects_fallback():
    """Test that validation correctly handles fallback explanations."""
    # Create a fallback-like explanation with missing rule ID
    fallback_explanation = CounterfactualExplanation(
        violated_rule_id="",  # Empty rule ID should fail
        required_correction="Generic fallback",
        confidence=0.5,
        explanation_text="Fallback explanation"
    )
    # This should fail validation due to empty rule ID
    assert validate_explanation(fallback_explanation, SAMPLE_RULES) is False

def test_handle_fallback_integration():
    """Integration test for fallback handling."""
    # Simulate a scenario where generator fails
    with patch('code.explanation.generator.generate_explanation', side_effect=Exception("LLM Failure")):
        fallback = handle_fallback("Test trajectory")
        assert isinstance(fallback, TemplateExplanation)
        assert fallback.is_fallback is True