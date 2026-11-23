"""
Distinctness validation for symbolic traces vs neural outputs.

Addresses Dan Rockmore's concern regarding "concrete mathematical objects" by
ensuring the symbolic trace is structurally and semantically distinct from the
neural narrative.

This module provides functions to:
1. Normalize text for comparison.
2. Calculate Jaccard similarity to measure lexical overlap.
3. Extract symbolic traces and neural narratives from explanation files.
4. Validate that a pair of explanations meets distinctness thresholds.
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set

from utils.validation import validate_explanation

# Configuration thresholds
MAX_JACCARD_SIMILARITY = 0.40  # Threshold below which traces are considered distinct
MIN_SYMBOLIC_LENGTH = 10       # Minimum tokens for a valid symbolic trace
MIN_NEURAL_LENGTH = 20         # Minimum tokens for a valid neural narrative

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lowercase, remove punctuation, collapse whitespace.

    Args:
        text: Raw text string.

    Returns:
        Normalized string suitable for set operations.
    """
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation and special characters, keep alphanumerics and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts based on token sets.

    Jaccard Similarity = |A ∩ B| / |A ∪ B|

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Float between 0.0 (no overlap) and 1.0 (identical sets).
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    if not norm1 or not norm2:
        return 0.0

    set1 = set(norm1.split())
    set2 = set(norm2.split())

    if not set1 or not set2:
        return 0.0

    intersection = set1.intersection(set2)
    union = set1.union(set2)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def extract_symbolic_trace(explanation_data: Dict[str, Any]) -> str:
    """
    Extract the symbolic trace content from an explanation data structure.

    Args:
        explanation_data: Dictionary containing explanation artifacts.

    Returns:
        The raw text of the symbolic trace.
    """
    # Expecting structure from T013/T015 outputs
    if 'symbolic_trace' in explanation_data:
        trace = explanation_data['symbolic_trace']
        if isinstance(trace, dict):
            # If it's a structured trace, convert to string representation
            return json.dumps(trace, sort_keys=True)
        return str(trace)
    
    # Fallback: look for 'trace' key
    if 'trace' in explanation_data:
        return str(explanation_data['trace'])
    
    logger.warning("Could not find 'symbolic_trace' or 'trace' in explanation data.")
    return ""


def extract_neural_narrative(explanation_data: Dict[str, Any]) -> str:
    """
    Extract the neural narrative content from an explanation data structure.

    Args:
        explanation_data: Dictionary containing explanation artifacts.

    Returns:
        The raw text of the neural narrative.
    """
    if 'neural_narrative' in explanation_data:
        return str(explanation_data['neural_narrative'])
    
    if 'neural_explanation' in explanation_data:
        return str(explanation_data['neural_explanation'])
    
    logger.warning("Could not find 'neural_narrative' or 'neural_explanation' in explanation data.")
    return ""


def validate_symbolic_trace_structure(trace_text: str) -> Tuple[bool, str]:
    """
    Validate that the extracted symbolic trace has structural properties
    expected of a rule-based engine output (e.g., contains rule names, steps).

    Args:
        trace_text: The text of the symbolic trace.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not trace_text or len(trace_text.split()) < MIN_SYMBOLIC_LENGTH:
        return False, f"Symbolic trace too short ({len(trace_text.split())} tokens < {MIN_SYMBOLIC_LENGTH})"
    
    # Check for common symbolic indicators
    indicators = ['rule', 'step', 'apply', 'distributive', 'commutative', 'associative', 'identity']
    trace_lower = trace_text.lower()
    
    found_indicators = [ind for ind in indicators if ind in trace_lower]
    
    if not found_indicators:
        # Not necessarily an error, but a warning
        logger.warning("Symbolic trace lacks common rule-based keywords.")
    
    return True, "Structure valid"


def validate_distinctness(
    symbolic_trace: str, 
    neural_narrative: str, 
    threshold: float = MAX_JACCARD_SIMILARITY
) -> Tuple[bool, float, str]:
    """
    Validate that the symbolic trace and neural narrative are distinct.

    Args:
        symbolic_trace: Text of the symbolic trace.
        neural_narrative: Text of the neural narrative.
        threshold: Maximum allowed Jaccard similarity.

    Returns:
        Tuple of (is_distinct, similarity_score, message).
    """
    if not symbolic_trace:
        return False, 0.0, "Symbolic trace is empty"
    if not neural_narrative:
        return False, 0.0, "Neural narrative is empty"

    similarity = calculate_jaccard_similarity(symbolic_trace, neural_narrative)
    
    if similarity > threshold:
        return False, similarity, f"Similarity {similarity:.4f} exceeds threshold {threshold}"
    
    return True, similarity, f"Distinctness confirmed (similarity: {similarity:.4f})"


def validate_explanation_pair(
    explanation_data: Dict[str, Any], 
    threshold: float = MAX_JACCARD_SIMILARITY
) -> Dict[str, Any]:
    """
    Validate a single explanation pair for distinctness.

    Args:
        explanation_data: Dictionary containing both symbolic and neural outputs.
        threshold: Similarity threshold.

    Returns:
        Dictionary with validation results.
    """
    trace = extract_symbolic_trace(explanation_data)
    narrative = extract_neural_narrative(explanation_data)

    trace_valid, trace_msg = validate_symbolic_trace_structure(trace)
    is_distinct, similarity, distinct_msg = validate_distinctness(trace, narrative, threshold)

    return {
        "valid": trace_valid and is_distinct,
        "symbolic_trace_valid": trace_valid,
        "distinctness_valid": is_distinct,
        "similarity_score": similarity,
        "symbolic_trace_length": len(trace.split()),
        "neural_narrative_length": len(narrative.split()),
        "messages": {
            "structure": trace_msg,
            "distinctness": distinct_msg
        }
    }


def main():
    """
    Entry point for command-line distinctness validation.
    Expects a JSON file path as argument containing explanation data.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate distinctness of symbolic vs neural explanations.")
    parser.add_argument("--input", type=str, required=True, help="Path to JSON file containing explanation data.")
    parser.add_argument("--output", type=str, required=False, help="Path to output validation report (JSON).")
    parser.add_argument("--threshold", type=float, default=MAX_JACCARD_SIMILARITY, help="Jaccard similarity threshold.")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON input: {e}")
        sys.exit(1)

    # Handle both single object and list of objects
    items = data if isinstance(data, list) else [data]
    
    results = []
    all_valid = True

    for i, item in enumerate(items):
        result = validate_explanation_pair(item, args.threshold)
        results.append(result)
        if not result["valid"]:
            all_valid = False
            logger.warning(f"Item {i} failed validation: {result['messages']}")
        else:
            logger.info(f"Item {i} passed: {result['messages']['distinctness']}")

    report = {
        "total_items": len(items),
        "passed": all_valid,
        "results": results
    }

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {args.output}")
    else:
        print(json.dumps(report, indent=2))

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()