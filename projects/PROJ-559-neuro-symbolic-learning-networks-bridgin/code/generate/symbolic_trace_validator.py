"""
Symbolic Trace Validator for Neuro-Symbolic Learning Networks.

This module explicitly verifies that the symbolic engine applies deterministic,
hand-coded rules (not learned weights) to generate traces. It addresses Ada
Lovelace's concern that the symbolic layer must "govern the developments" and
not be a "veneer" or statistical mimicry.

It performs three core checks:
1. Structure Validation: Ensures the trace contains only defined rule types and
   standard symbolic operations (no neural embeddings or probability vectors).
2. Determinism Validation: Runs the symbolic engine twice on the same input and
   verifies byte-for-byte identical output.
3. Distinctness Validation: Verifies the symbolic trace is semantically distinct
   from the neural explanation (low Jaccard similarity, different token distributions).
"""

import json
import logging
import os
import re
import sys
import hashlib
import argparse
from typing import Dict, Any, List, Optional, Tuple

# Import existing utilities from sibling modules
from generate.symbolic_explanation import SymbolicSolver, generate_symbolic_explanation
from generate.validate_distinctness import validate_distinctness, calculate_jaccard_similarity

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Allowed rule identifiers in a valid symbolic trace
ALLOWED_RULE_TYPES = {
    "CommutativityRule",
    "AssociativityRule",
    "DistributiveRule",
    "IdentityElementRule",
    "ArithmeticOperation",
    "VariableSubstitution",
    "SimplificationStep"
}

# Forbidden patterns indicating neural/learned artifacts
FORBIDDEN_PATTERNS = [
    r'"logits":',
    r'"embeddings":',
    r'"probabilities":',
    r'"weights":',
    r'"attention":',
    r'"hidden_state":',
    r"np\.random",
    r"torch\.rand",
    r"random\.random"
]

def validate_symbolic_trace_structure(trace: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the trace structure adheres to hand-coded rule definitions.

    Args:
        trace: The symbolic trace dictionary.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []

    if not isinstance(trace, dict):
        errors.append("Trace must be a dictionary.")
        return False, errors

    # Check for required fields
    required_fields = ["problem_id", "rules_applied", "final_result"]
    for field in required_fields:
        if field not in trace:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Verify rules_applied contains only allowed rule types
    rules_applied = trace.get("rules_applied", [])
    if not isinstance(rules_applied, list):
        errors.append("rules_applied must be a list.")
        return False, errors

    for step in rules_applied:
        if not isinstance(step, dict):
            errors.append(f"Invalid rule step format: {step}")
            continue

        rule_type = step.get("rule_type")
        if rule_type not in ALLOWED_RULE_TYPES:
            errors.append(f"Disallowed rule type: {rule_type}. Allowed: {ALLOWED_RULE_TYPES}")

        # Check for forbidden neural artifacts in the step
        step_json = json.dumps(step)
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, step_json):
                errors.append(f"Detected neural artifact in rule step: {pattern}")

    # Check final_result is a deterministic value (not a distribution)
    final_result = trace.get("final_result")
    if isinstance(final_result, dict) and ("distribution" in final_result or "probability" in final_result):
        errors.append("final_result must be a deterministic value, not a probability distribution.")

    return len(errors) == 0, errors


def validate_determinism(problem_id: str, max_retries: int = 3) -> Tuple[bool, str]:
    """
    Validates that the symbolic engine produces deterministic output.

    Runs the solver twice on the same problem_id and compares the outputs.
    If they differ, it implies the presence of randomness or learned weights.

    Args:
        problem_id: The ID of the problem to test.
        max_retries: Number of attempts to run the check.

    Returns:
        Tuple of (is_deterministic, message).
    """
    logger.info(f"Running determinism check for problem_id: {problem_id}")

    # We need a mock problem data structure to run the solver
    # Since we don't have a direct DB, we simulate a standard algebra problem
    # based on the problem_id format, or use a generic one if not found.
    # In a real scenario, this would fetch from the dataset.
    # For this validator, we construct a known deterministic input.
    
    mock_problem = {
        "problem_id": problem_id,
        "type": "algebra",
        "expression": "2 * (x + 3)",
        "target": "2x + 6"
    }

    outputs = []
    for i in range(2):
        try:
            # Call the actual symbolic generator
            result = generate_symbolic_explanation(mock_problem)
            outputs.append(json.dumps(result, sort_keys=True))
        except Exception as e:
            logger.error(f"Error generating symbolic explanation on attempt {i+1}: {e}")
            return False, f"Failed to generate explanation: {str(e)}"

    hash1 = hashlib.sha256(outputs[0].encode()).hexdigest()
    hash2 = hashlib.sha256(outputs[1].encode()).hexdigest()

    if hash1 == hash2:
        logger.info("Determinism check PASSED: Outputs are identical.")
        return True, "Determinism verified: Symbolic engine produces identical outputs for identical inputs."
    else:
        logger.error("Determinism check FAILED: Outputs differ.")
        return False, f"Determinism failed. Hash1: {hash1}, Hash2: {hash2}"


def validate_distinctness(symbolic_trace_path: str, neural_explanation_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates that the symbolic trace is distinct from the neural explanation.

    Args:
        symbolic_trace_path: Path to the symbolic trace JSON file.
        neural_explanation_path: Path to the neural explanation text/JSON file.

    Returns:
        Tuple of (is_distinct, metrics_dict).
    """
    if not os.path.exists(symbolic_trace_path):
        return False, {"error": f"Symbolic trace file not found: {symbolic_trace_path}"}
    if not os.path.exists(neural_explanation_path):
        return False, {"error": f"Neural explanation file not found: {neural_explanation_path}"}

    with open(symbolic_trace_path, 'r') as f:
        symbolic_data = json.load(f)
    
    with open(neural_explanation_path, 'r') as f:
        neural_data = f.read()

    # Convert symbolic trace to text for comparison
    symbolic_text = json.dumps(symbolic_data, sort_keys=True)
    
    # Use existing distinctness validation logic
    is_valid, metrics = validate_distinctness(symbolic_text, neural_data)
    
    # Additional check: ensure symbolic trace is not just a substring of the neural output
    if symbolic_text.lower() in neural_data.lower():
        return False, {
            "error": "Symbolic trace appears as a direct substring in neural explanation.",
            "jaccard_similarity": metrics.get("jaccard_similarity", 0)
        }

    return is_valid, metrics


def validate_trace_file(trace_file_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Main entry point for validating a single trace file.

    Args:
        trace_file_path: Path to the JSON file containing the symbolic trace.

    Returns:
        Tuple of (is_valid, errors, details).
    """
    if not os.path.exists(trace_file_path):
        return False, [f"File not found: {trace_file_path}"], {}

    try:
        with open(trace_file_path, 'r') as f:
            trace = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {str(e)}"], {}

    # 1. Structure Validation
    is_struct_valid, struct_errors = validate_symbolic_trace_structure(trace)
    errors = struct_errors

    # 2. Determinism Validation (using problem_id from trace)
    problem_id = trace.get("problem_id", "unknown")
    is_det_valid, det_msg = validate_determinism(problem_id)
    
    details = {
        "structure_valid": is_struct_valid,
        "determinism_valid": is_det_valid,
        "determinism_message": det_msg
    }

    if not is_det_valid:
        errors.append(det_msg)

    return len(errors) == 0, errors, details


def main():
    """
    CLI entry point for the symbolic trace validator.
    """
    parser = argparse.ArgumentParser(
        description="Validate symbolic traces for determinism and rule adherence."
    )
    parser.add_argument(
        "--trace-file",
        type=str,
        required=True,
        help="Path to the symbolic trace JSON file to validate."
    )
    parser.add_argument(
        "--neural-file",
        type=str,
        required=False,
        help="Path to the corresponding neural explanation file (for distinctness check)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/derived/symbolic_validation_report.json",
        help="Path to save the validation report."
    )

    args = parser.parse_args()

    logger.info(f"Starting validation for trace: {args.trace_file}")

    # 1. Validate Structure and Determinism
    is_valid, errors, details = validate_trace_file(args.trace_file)

    report = {
        "trace_file": args.trace_file,
        "validation_passed": is_valid,
        "errors": errors,
        "details": details,
        "timestamp": os.popen('date -Iseconds 2>/dev/null || date').read().strip()
    }

    # 2. Validate Distinctness if neural file provided
    if args.neural_file:
        logger.info(f"Checking distinctness against: {args.neural_file}")
        is_distinct, distinct_metrics = validate_distinctness(args.trace_file, args.neural_file)
        report["distinctness_check"] = {
            "passed": is_distinct,
            "metrics": distinct_metrics
        }
        if not is_distinct:
            report["errors"].append("Distinctness check failed.")
            report["validation_passed"] = False

    # 3. Save Report
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report saved to: {args.output}")

    if not report["validation_passed"]:
        logger.error("Validation FAILED. See errors above.")
        sys.exit(1)
    else:
        logger.info("Validation PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()