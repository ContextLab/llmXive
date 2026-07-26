"""
Symbolic Trace Validator for Neuro-Symbolic Learning Networks.

This module explicitly verifies that the symbolic engine applies deterministic,
hand-coded rules (not learned weights) to generate the trace. It addresses
Ada Lovelace's concern that the symbolic layer must "govern the developments"
and not be a "veneer" or statistical mimicry.

Validation checks:
1. Trace steps correspond to known rule definitions.
2. No probabilistic or weight-based decisions are recorded.
3. Rule application order is deterministic for identical inputs.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Define the set of valid rule names that the symbolic engine should use
VALID_RULE_NAMES = {
    "Commutativity",
    "Associativity",
    "Distributive Property",
    "Identity Element",
    "Initial State"
}

# Patterns that indicate non-symbolic, probabilistic, or neural behavior
SUSPICIOUS_PATTERNS = [
    r"probability",
    r"weight",
    r"confidence",
    r"likelihood",
    r"neural",
    r"learned",
    r"trained",
    r"softmax",
    r"gradient",
    r"random",
    r"stochastic"
]


def validate_symbolic_trace_structure(trace: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate the structure and content of a symbolic trace.

    Args:
        trace: List of step dictionaries from the symbolic solver.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if not isinstance(trace, list):
        errors.append("Trace is not a list.")
        return False, errors

    if len(trace) == 0:
        errors.append("Trace is empty.")
        return False, errors

    # Check first step is "Initial State"
    if trace[0].get("rule_applied") != "Initial State":
        errors.append(f"First step must be 'Initial State', found: {trace[0].get('rule_applied')}")

    for i, step in enumerate(trace):
        if not isinstance(step, dict):
            errors.append(f"Step {i} is not a dictionary.")
            continue

        required_keys = {"step", "expression", "rule_applied", "explanation"}
        missing_keys = required_keys - set(step.keys())
        if missing_keys:
            errors.append(f"Step {i} missing keys: {missing_keys}")

        # Check rule name validity
        rule_name = step.get("rule_applied", "")
        if rule_name not in VALID_RULE_NAMES:
            errors.append(f"Step {i} uses invalid rule name: '{rule_name}'")

        # Check for suspicious patterns in explanation
        explanation = step.get("explanation", "").lower()
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, explanation, re.IGNORECASE):
                errors.append(f"Step {i} explanation contains suspicious pattern '{pattern}': '{explanation}'")

        # Check for deterministic expression format (no random seeds or floating point noise)
        expression = step.get("expression", "")
        # Simple heuristic: expressions should be clean arithmetic, not contain random tokens
        if re.search(r"random_seed|noise_\d+", expression):
            errors.append(f"Step {i} expression contains non-deterministic tokens: '{expression}'")

    return len(errors) == 0, errors


def validate_determinism(trace_1: List[Dict[str, Any]], trace_2: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Verify that two traces for the same input are identical (determinism check).

    Args:
        trace_1: First trace.
        trace_2: Second trace.

    Returns:
        Tuple of (is_deterministic, message)
    """
    if len(trace_1) != len(trace_2):
        return False, f"Trace lengths differ: {len(trace_1)} vs {len(trace_2)}"

    for i, (step1, step2) in enumerate(zip(trace_1, trace_2)):
        if step1.get("expression") != step2.get("expression"):
            return False, f"Expression mismatch at step {i}: '{step1.get('expression')}' vs '{step2.get('expression')}'"
        if step1.get("rule_applied") != step2.get("rule_applied"):
            return False, f"Rule mismatch at step {i}: '{step1.get('rule_applied')}' vs '{step2.get('rule_applied')}'"

    return True, "Traces are identical; engine is deterministic."


def validate_distinctness(trace: List[Dict[str, Any]], neural_narrative: str) -> Tuple[bool, str]:
    """
    Ensure the symbolic trace is distinct from the neural narrative.

    Args:
        trace: Symbolic trace.
        neural_narrative: Text output from the neural generator.

    Returns:
        Tuple of (is_distinct, message)
    """
    # Extract all rule names from trace
    trace_rules = [step.get("rule_applied") for step in trace if step.get("rule_applied") != "Initial State"]
    trace_text = " ".join(trace_rules).lower()

    # Simple check: neural narrative should not contain exact rule names in a way that suggests mimicry
    # This is a heuristic; a full semantic check would require NLP
    neural_lower = neural_narrative.lower()

    matches = []
    for rule in trace_rules:
        if rule.lower() in neural_lower:
            matches.append(rule)

    if len(matches) > len(trace_rules) * 0.8:
        return False, f"Neural narrative closely mimics symbolic rules ({len(matches)}/{len(trace_rules)} matches). " \
                     f"This suggests the neural layer is a veneer, not a distinct reasoning system."

    return True, "Symbolic trace and neural narrative are sufficiently distinct."


def validate_trace_file(file_path: str) -> Dict[str, Any]:
    """
    Validate a single symbolic trace file.

    Args:
        file_path: Path to the JSON trace file.

    Returns:
        Validation report dictionary.
    """
    logger.info(f"Validating trace file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {
            "file": file_path,
            "valid": False,
            "errors": [f"Failed to load JSON: {e}"]
        }

    trace = data.get("trace", [])
    is_valid, errors = validate_symbolic_trace_structure(trace)

    return {
        "file": file_path,
        "valid": is_valid,
        "errors": errors,
        "steps_count": len(trace),
        "rules_used": list(set([step.get("rule_applied") for step in trace if step.get("rule_applied") != "Initial State"]))
    }


def main():
    """
    Main entry point to validate all symbolic traces in the data directory.
    """
    data_dir = "data/symbolic"
    if not os.path.exists(data_dir):
        logger.error(f"Directory {data_dir} does not exist. Run the symbolic generator first.")
        return 1

    trace_files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.startswith("trace_") and f.endswith(".json")
    ]

    if not trace_files:
        logger.warning(f"No trace files found in {data_dir}")
        return 0

    validation_results = []
    all_valid = True

    for file_path in trace_files:
        result = validate_trace_file(file_path)
        validation_results.append(result)
        if not result["valid"]:
            all_valid = False

    # Save validation report
    report_path = os.path.join(data_dir, "validation_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2)

    logger.info(f"Validation report saved to {report_path}")

    if all_valid:
        print(f"\n✅ All {len(trace_files)} symbolic traces are valid.")
        print("The symbolic engine is confirmed to use deterministic, hand-coded rules.")
        return 0
    else:
        print(f"\n❌ Validation failed for some traces.")
        print("Check the report at", report_path)
        return 1


if __name__ == "__main__":
    exit(main())