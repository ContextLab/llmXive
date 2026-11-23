import re
from typing import Dict, Any, List

from models.data_models import StructuralElementCount
from utils.logger import get_logger

logger = get_logger(__name__)

def count_structural_elements(prompt_text: str) -> StructuralElementCount:
    """
    Dynamically count structural elements in a prompt:
    - examples: Count of '>>>' or 'Example:' occurrences
    - constraints: Count of 'Constraint:', 'Note:', 'Warning:', 'Important:'
    - steps: Count of 'Step:', 'Instruction:', 'First:', 'Next:', 'Then:'

    Returns a StructuralElementCount object.
    """
    text_lower = prompt_text.lower()

    # Count examples
    example_patterns = [
        r">>>",
        r"example\s*:",
        r"sample\s*:",
    ]
    example_count = 0
    for pattern in example_patterns:
        matches = re.findall(pattern, text_lower)
        example_count += len(matches)
    
    # Count constraints
    constraint_patterns = [
        r"constraint\s*:",
        r"note\s*:",
        r"warning\s*:",
        r"important\s*:",
        r"critical\s*:",
        r"requirement\s*:",
    ]
    constraint_count = sum(len(re.findall(p, text_lower)) for p in constraint_patterns)

    # Count steps
    step_patterns = [
        r"step\s*:\s*\d+",
        r"step\s+\d+",
        r"instruction\s*:\s*\d+",
        r"instruction\s+\d+",
        r"first\s*:",
        r"next\s*:",
        r"then\s*:",
    ]
    step_count = sum(len(re.findall(p, text_lower)) for p in step_patterns)

    return StructuralElementCount(
        examples=example_count,
        constraints=constraint_count,
        steps=step_count,
    )

def analyze_prompt_structure(prompt_text: str) -> Dict[str, Any]:
    """
    Return a detailed analysis of the prompt structure.
    Calculates a complexity score based on element counts and text length.
    """
    counts = count_structural_elements(prompt_text)
    total_elements = counts.examples + counts.constraints + counts.steps

    # Complexity score formula: weighted sum of elements + normalized token length proxy
    # This provides a scalar metric for correlation analysis later
    complexity_score = (
        (counts.examples * 15) + 
        (counts.constraints * 10) + 
        (counts.steps * 20) + 
        (len(prompt_text) / 100)
    )

    return {
        "examples": counts.examples,
        "constraints": counts.constraints,
        "steps": counts.steps,
        "total_elements": total_elements,
        "complexity_score": complexity_score,
    }