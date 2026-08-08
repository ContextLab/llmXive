"""
Critique Templates for Socratic Dialogue Generation.

Defines deterministic prompt templates for identifying logical contradictions
in mathematical reasoning steps. These templates are filled with model-derived
evidence to generate critiques.

Error Types:
- calculation_error: Arithmetic or algebraic miscalculations.
- logic_gap: Missing steps or non-sequiturs in reasoning.
- unsupported_assumption: Claims made without justification or evidence.
"""

from typing import Dict, List, Any

ERROR_TYPES: List[str] = ["calculation_error", "logic_gap", "unsupported_assumption"]

TEMPLATES: Dict[str, str] = {
    "calculation_error": (
        "The step claiming '{step_content}' contains a calculation error. "
        "Specifically, {evidence} contradicts the arithmetic rules required here. "
        "The correct computation should be {correct_computation}."
    ),
    "logic_gap": (
        "The reasoning jumps from '{premise}' to '{conclusion}' without sufficient logical connection. "
        "The evidence suggests that {evidence}, which creates a gap in the argument. "
        "A valid derivation would require intermediate steps showing {missing_logic}."
    ),
    "unsupported_assumption": (
        "The argument assumes '{assumption}' without justification. "
        "The provided evidence {evidence} does not support this claim. "
        "This assumption is critical because {impact}, and it cannot be taken for granted."
    )
}

def get_template(error_type: str) -> str:
    """
    Retrieves the prompt template for a specific error type.

    Args:
        error_type: One of the defined ERROR_TYPES.

    Returns:
        The string template for the error type.

    Raises:
        ValueError: If the error_type is not recognized.
    """
    if error_type not in TEMPLATES:
        raise ValueError(f"Unknown error type: {error_type}. Must be one of {ERROR_TYPES}")
    return TEMPLATES[error_type]

def validate_template_fields(error_type: str, fields: Dict[str, Any]) -> bool:
    """
    Validates that the provided fields match the placeholders in the template.

    Args:
        error_type: The type of error.
        fields: Dictionary of field values to be filled into the template.

    Returns:
        True if all placeholders in the template are present in fields.
    """
    template = get_template(error_type)
    # Simple check for curly brace placeholders
    import re
    placeholders = set(re.findall(r'\{(\w+)\}', template))
    return placeholders.issubset(set(fields.keys()))
