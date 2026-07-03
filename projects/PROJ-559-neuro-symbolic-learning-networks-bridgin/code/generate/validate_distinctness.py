import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from utils.validation import validate_explanation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thresholds for distinctness validation (addressing Rockmore's concern)
# Jaccard similarity threshold: traces must be distinct enough
JACCARD_THRESHOLD = 0.4
# Minimum length difference to ensure structural distinctness
MIN_LENGTH_DIFF_RATIO = 0.2

def normalize_text(text: str) -> str:
    """Normalize text for comparison by lowercasing and removing extra whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts based on word sets.
    Returns a value between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0

    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    if not union:
        return 0.0

    return len(intersection) / len(union)

def extract_symbolic_trace(explanation: Dict[str, Any]) -> str:
    """
    Extract the symbolic trace from an explanation dictionary.
    The symbolic trace should contain rule applications and logical steps.
    """
    if not explanation:
        return ""

    # Try to extract from 'symbolic_trace' key first
    if 'symbolic_trace' in explanation and explanation['symbolic_trace']:
        trace = explanation['symbolic_trace']
        if isinstance(trace, list):
            return " ".join(str(step) for step in trace)
        return str(trace)

    # Fallback: look for rule-based content in 'steps' or 'reasoning'
    if 'steps' in explanation and explanation['steps']:
        steps = explanation['steps']
        if isinstance(steps, list):
            return " ".join(str(step) for step in steps)

    # If no structured trace, return the raw explanation text for analysis
    if 'explanation_text' in explanation:
        return str(explanation['explanation_text'])

    return ""

def extract_neural_narrative(explanation: Dict[str, Any]) -> str:
    """
    Extract the neural narrative from an explanation dictionary.
    The neural narrative should contain the fluent, natural language explanation.
    """
    if not explanation:
        return ""

    # Try to extract from 'neural_narrative' key first
    if 'neural_narrative' in explanation and explanation['neural_narrative']:
        return str(explanation['neural_narrative'])

    # Fallback: look for 'explanation_text' or 'narrative'
    if 'explanation_text' in explanation:
        return str(explanation['explanation_text'])

    if 'narrative' in explanation:
        return str(explanation['narrative'])

    # Last resort: return the whole explanation as string
    return json.dumps(explanation, indent=2)

def validate_symbolic_trace_structure(trace: str) -> Tuple[bool, str]:
    """
    Validate that the symbolic trace has a proper structure (rule applications).
    Returns (is_valid, message).
    """
    if not trace or len(trace.strip()) == 0:
        return False, "Symbolic trace is empty"

    # Check for rule-related keywords that indicate symbolic reasoning
    rule_keywords = [
        'rule', 'commutativity', 'associativity', 'distributive',
        'identity', 'step', 'apply', 'property', 'law', 'equation'
    ]

    trace_lower = trace.lower()
    has_rule_keyword = any(keyword in trace_lower for keyword in rule_keywords)

    if not has_rule_keyword:
        return False, "Symbolic trace lacks rule-based structure (no rule keywords found)"

    # Check for structured steps (e.g., numbered steps or bullet points)
    has_structure = bool(re.search(r'\d+\.|\-|\*', trace)) or 'step' in trace_lower

    if not has_structure:
        return False, "Symbolic trace lacks structured steps"

    return True, "Symbolic trace structure is valid"

def validate_distinctness(symbolic_trace: str, neural_narrative: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that symbolic traces are distinct from neural outputs.
    This addresses Rockmore's concern about 'concrete mathematical objects' -
    the symbolic layer must be genuinely distinct, not just a rephrasing.

    Returns (is_valid, details_dict).
    """
    details = {
        'symbolic_trace_length': len(symbolic_trace),
        'neural_narrative_length': len(neural_narrative),
        'jaccard_similarity': 0.0,
        'issues': []
    }

    if not symbolic_trace:
        details['issues'].append("Symbolic trace is empty")
        return False, details

    if not neural_narrative:
        details['issues'].append("Neural narrative is empty")
        return False, details

    # Calculate Jaccard similarity
    jaccard_sim = calculate_jaccard_similarity(symbolic_trace, neural_narrative)
    details['jaccard_similarity'] = jaccard_sim

    # Check 1: Jaccard similarity must be below threshold
    if jaccard_sim > JACCARD_THRESHOLD:
        details['issues'].append(
            f"Jaccard similarity ({jaccard_sim:.3f}) exceeds threshold ({JACCARD_THRESHOLD}). "
            "Symbolic and neural outputs are too similar."
        )

    # Check 2: Length difference ratio
    min_len = min(len(symbolic_trace), len(neural_narrative))
    max_len = max(len(symbolic_trace), len(neural_narrative))

    if min_len > 0:
        length_diff_ratio = (max_len - min_len) / max_len
        if length_diff_ratio < MIN_LENGTH_DIFF_RATIO:
            details['issues'].append(
                f"Length difference ratio ({length_diff_ratio:.3f}) is too small. "
                "Symbolic and neural outputs should have distinct structures."
            )

    # Check 3: Structural distinctness
    # Symbolic should have rule keywords, neural should not be just a copy
    symbolic_keywords = set(re.findall(r'\b\w+\b', symbolic_trace.lower()))
    neural_keywords = set(re.findall(r'\b\w+\b', neural_narrative.lower()))

    # If neural narrative contains too many symbolic-specific terms without context, it might be a copy
    symbolic_specific = {'rule', 'commutativity', 'associativity', 'distributive', 'identity'}
    overlap_with_symbolic_specific = symbolic_specific.intersection(neural_keywords)

    if len(overlap_with_symbolic_specific) > 3 and jaccard_sim > 0.3:
        details['issues'].append(
            "Neural narrative contains too many symbolic-specific terms without proper context. "
            "This suggests the neural output may be a rephrasing rather than a distinct explanation."
        )

    is_valid = len(details['issues']) == 0
    return is_valid, details

def validate_explanation_pair(
    symbolic_explanation: Dict[str, Any],
    neuro_symbolic_explanation: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the symbolic trace in a neuro-symbolic explanation is distinct
    from the neural narrative component.

    Args:
        symbolic_explanation: The pure symbolic explanation output
        neuro_symbolic_explanation: The neuro-symbolic explanation output

    Returns:
        (is_valid, validation_details)
    """
    details = {
        'symbolic_trace_valid': False,
        'neural_narrative_valid': False,
        'distinctness_valid': False,
        'details': {}
    }

    # Extract components
    symbolic_trace = extract_symbolic_trace(neuro_symbolic_explanation)
    neural_narrative = extract_neural_narrative(neuro_symbolic_explanation)

    # Validate symbolic trace structure
    trace_valid, trace_msg = validate_symbolic_trace_structure(symbolic_trace)
    details['symbolic_trace_valid'] = trace_valid
    if not trace_valid:
        details['details']['trace_structure'] = trace_msg

    # Validate distinctness
    distinctness_valid, distinctness_details = validate_distinctness(
        symbolic_trace, neural_narrative
    )
    details['distinctness_valid'] = distinctness_valid
    details['details'].update(distinctness_details)

    # Overall validation
    is_valid = trace_valid and distinctness_valid

    if not is_valid:
        logger.warning(
            f"Distinctness validation failed: {details['details'].get('issues', [])}"
        )
    else:
        logger.info("Distinctness validation passed: symbolic and neural outputs are distinct")

    return is_valid, details

def main():
    """
    Main function to run distinctness validation on explanation pairs.
    This can be used as a standalone script or imported as a module.
    """
    import sys

    # Example usage: validate a pair of explanations
    sample_symbolic = {
        "problem_id": "123",
        "symbolic_trace": [
            "Step 1: Apply commutativity rule: a + b = b + a",
            "Step 2: Apply associativity rule: (a + b) + c = a + (b + c)",
            "Step 3: Apply distributive rule: a * (b + c) = a*b + a*c"
        ],
        "explanation_text": "Using commutativity, associativity, and distributive properties..."
    }

    sample_neuro_symbolic = {
        "problem_id": "123",
        "neural_narrative": "To solve this problem, we can rearrange the terms using the commutative property, "
                            "then group them with the associative property, and finally distribute the multiplication.",
        "symbolic_trace": [
            "Step 1: Apply commutativity rule: a + b = b + a",
            "Step 2: Apply associativity rule: (a + b) + c = a + (b + c)",
            "Step 3: Apply distributive rule: a * (b + c) = a*b + a*c"
        ],
        "explanation_text": "The solution involves applying mathematical rules to simplify the expression."
    }

    # Validate the pair
    is_valid, details = validate_explanation_pair(sample_symbolic, sample_neuro_symbolic)

    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
    print(f"Details: {json.dumps(details, indent=2)}")

    if not is_valid:
        sys.exit(1)

if __name__ == "__main__":
    main()
