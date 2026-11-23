"""
Counterfactual explanation validation module.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import re

class CounterfactualExplanation(BaseModel):
    """
    Pydantic model for counterfactual explanations.
    """
    violated_rule_id: str = Field(..., description="ID of the violated rule")
    required_correction: str = Field(..., description="Required correction")
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation_text: str = Field(..., description="Natural language explanation")

    @field_validator('violated_rule_id')
    @classmethod
    def rule_id_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Rule ID cannot be empty")
        return v

def validate_explanation(explanation: CounterfactualExplanation, rules: Dict[str, Any]) -> bool:
    """
    Validate a counterfactual explanation against ground-truth rules.

    This function performs two levels of validation:
    1. Structural validation (already handled by Pydantic model instantiation)
    2. Semantic validation against the provided rules dictionary:
       - Verifies that the violated_rule_id exists in the rules dictionary
       - Checks that the explanation_text contains the rule_id (consistency check)
       - Validates that confidence is within acceptable bounds (already handled by Field)

    Args:
        explanation: The explanation to validate.
        rules: Ground-truth environment rules dictionary where keys are rule IDs.

    Returns:
        True if the explanation is valid against the rules, False otherwise.
    """
    if not explanation or not rules:
        return False

    # Check if the violated_rule_id exists in the provided rules
    rule_id = explanation.violated_rule_id
    if rule_id not in rules:
        return False

    # Verify the rule ID is present in the explanation text for consistency
    # This prevents hallucinated rule IDs that might pass schema validation
    # but don't actually reference the rule in the narrative
    if rule_id.lower() not in explanation.explanation_text.lower():
        # Allow partial matches or common variations
        if not re.search(rf"\b{re.escape(rule_id)}\b", explanation.explanation_text, re.IGNORECASE):
            return False

    # Ensure required_correction is not empty
    if not explanation.required_correction or not explanation.required_correction.strip():
        return False

    return True
