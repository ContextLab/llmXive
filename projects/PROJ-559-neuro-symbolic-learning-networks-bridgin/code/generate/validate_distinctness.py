"""
Validation module to ensure symbolic traces are distinct from neural outputs.
Addresses Rockmore's "concrete mathematical objects" concern by verifying that
the symbolic layer provides a rule-based, deterministic trace that is structurally
and semantically distinct from the neural narrative.
"""
import os
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set

from utils.validation import validate_explanation

logger = logging.getLogger(__name__)

# Thresholds for distinctness metrics
MIN_SIMILARITY_SCORE = 0.0
MAX_OVERLAP_RATIO = 0.7
MIN_SYMBOLIC_LENGTH = 10
MIN_NEURAL_LENGTH = 20

def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, remove punctuation, split into tokens."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = text.split()
    return set(tokens)

def calculate_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets of tokens."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def extract_symbolic_trace(explanation_data: Dict[str, Any]) -> str:
    """Extract the symbolic trace from an explanation data structure."""
    if "symbolic_trace" in explanation_data:
        return json.dumps(explanation_data["symbolic_trace"], indent=2)
    elif "trace" in explanation_data:
        return json.dumps(explanation_data["trace"], indent=2)
    elif "steps" in explanation_data:
        return json.dumps(explanation_data["steps"], indent=2)
    return ""

def extract_neural_narrative(explanation_data: Dict[str, Any]) -> str:
    """Extract the neural narrative from an explanation data structure."""
    if "neural_narrative" in explanation_data:
        return explanation_data["neural_narrative"]
    elif "narrative" in explanation_data:
        return explanation_data["narrative"]
    elif "explanation" in explanation_data:
        return explanation_data["explanation"]
    return ""

def validate_symbolic_trace_structure(trace_data: Any) -> Tuple[bool, List[str]]:
    """
    Validate that the symbolic trace has a proper rule-based structure.
    Checks for:
    - Presence of rule applications (e.g., "rule", "rule_name", "applied_rule")
    - Deterministic steps (e.g., "step", "operation", "transform")
    - Mathematical objects (e.g., "operand", "value", "expression")
    """
    issues = []
    if not isinstance(trace_data, list):
        issues.append("Symbolic trace is not a list of steps")
        return False, issues

    rule_keywords = {"rule", "rule_name", "applied_rule", "rule_type", "operation"}
    step_keywords = {"step", "operation", "transform", "apply"}
    math_keywords = {"operand", "value", "expression", "result", "left", "right"}

    has_rule = False
    has_step = False
    has_math = False

    for step in trace_data:
        if isinstance(step, dict):
            keys = set(k.lower() for k in step.keys())
            if any(k in keys for k in rule_keywords):
                has_rule = True
            if any(k in keys for k in step_keywords):
                has_step = True
            if any(k in keys for k in math_keywords):
                has_math = True

    if not has_rule:
        issues.append("Symbolic trace lacks rule application markers")
    if not has_step:
        issues.append("Symbolic trace lacks step/operation markers")
    if not has_math:
        issues.append("Symbolic trace lacks mathematical object references")

    return len(issues) == 0, issues

def validate_distinctness(
    symbolic_data: Dict[str, Any],
    neural_data: Dict[str, Any],
    threshold: float = 0.7
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that symbolic traces are distinct from neural outputs.

    Returns:
        Tuple of (is_valid, report_dict)
        report_dict contains:
            - similarity_score: Jaccard similarity between token sets
            - overlap_ratio: Ratio of shared tokens to total unique tokens
            - symbolic_structure_valid: Whether symbolic trace has proper structure
            - length_check: Whether both outputs meet minimum length requirements
            - issues: List of validation issues
    """
    issues = []
    report = {
        "similarity_score": 0.0,
        "overlap_ratio": 0.0,
        "symbolic_structure_valid": False,
        "length_check": False,
        "issues": []
    }

    # Extract content
    symbolic_trace = extract_symbolic_trace(symbolic_data)
    neural_narrative = extract_neural_narrative(neural_data)

    # Check lengths
    if len(symbolic_trace) < MIN_SYMBOLIC_LENGTH:
        issues.append(f"Symbolic trace too short ({len(symbolic_trace)} < {MIN_SYMBOLIC_LENGTH})")
    if len(neural_narrative) < MIN_NEURAL_LENGTH:
        issues.append(f"Neural narrative too short ({len(neural_narrative)} < {MIN_NEURAL_LENGTH})")

    report["length_check"] = (
        len(symbolic_trace) >= MIN_SYMBOLIC_LENGTH and
        len(neural_narrative) >= MIN_NEURAL_LENGTH
    )

    # Normalize and compare
    symbolic_tokens = normalize_text(symbolic_trace)
    neural_tokens = normalize_text(neural_narrative)

    jaccard = calculate_jaccard_similarity(symbolic_tokens, neural_tokens)
    report["similarity_score"] = jaccard

    if jaccard > threshold:
        issues.append(f"Similarity score too high: {jaccard:.3f} > {threshold}")

    # Calculate overlap ratio
    if len(symbolic_tokens) > 0 and len(neural_tokens) > 0:
        overlap = len(symbolic_tokens.intersection(neural_tokens))
        union = len(symbolic_tokens.union(neural_tokens))
        overlap_ratio = overlap / union if union > 0 else 0.0
        report["overlap_ratio"] = overlap_ratio

        if overlap_ratio > MAX_OVERLAP_RATIO:
            issues.append(f"Token overlap too high: {overlap_ratio:.3f} > {MAX_OVERLAP_RATIO}")

    # Validate symbolic structure
    trace_data = symbolic_data.get("symbolic_trace", symbolic_data.get("trace", []))
    if isinstance(trace_data, list):
        is_valid, struct_issues = validate_symbolic_trace_structure(trace_data)
        report["symbolic_structure_valid"] = is_valid
        issues.extend(struct_issues)
    else:
        issues.append("Symbolic trace is not a valid list structure")
        report["symbolic_structure_valid"] = False

    report["issues"] = issues
    is_valid = len(issues) == 0

    return is_valid, report

def validate_explanation_pair(
    symbolic_path: str,
    neural_path: str,
    output_path: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Load two explanation files and validate their distinctness.

    Args:
        symbolic_path: Path to symbolic explanation JSON
        neural_path: Path to neural explanation JSON
        output_path: Optional path to write validation report JSON

    Returns:
        Tuple of (is_valid, report_dict)
    """
    # Load files
    with open(symbolic_path, 'r', encoding='utf-8') as f:
        symbolic_data = json.load(f)

    with open(neural_path, 'r', encoding='utf-8') as f:
        neural_data = json.load(f)

    # Validate distinctness
    is_valid, report = validate_distinctness(symbolic_data, neural_data)

    # Add file metadata
    report["symbolic_file"] = symbolic_path
    report["neural_file"] = neural_path
    report["validation_passed"] = is_valid

    # Write report if requested
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report written to {output_path}")

    return is_valid, report

def main():
    """Main entry point for standalone execution."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Validate distinctness between symbolic and neural explanations"
    )
    parser.add_argument(
        "--symbolic",
        required=True,
        help="Path to symbolic explanation JSON file"
    )
    parser.add_argument(
        "--neural",
        required=True,
        help="Path to neural explanation JSON file"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write validation report JSON (optional)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Maximum allowed similarity score (default: 0.7)"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        is_valid, report = validate_explanation_pair(
            args.symbolic,
            args.neural,
            args.output
        )

        print(json.dumps(report, indent=2))

        if not is_valid:
            logger.error("Validation failed: symbolic and neural outputs are not sufficiently distinct")
            sys.exit(1)
        else:
            logger.info("Validation passed: symbolic and neural outputs are distinct")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()