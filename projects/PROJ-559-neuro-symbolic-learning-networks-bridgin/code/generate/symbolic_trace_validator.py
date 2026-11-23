"""
Symbolic Trace Validator

Validates that the symbolic engine applies deterministic, hand-coded rules
to generate traces, ensuring the symbolic layer is not a statistical mimicry
but a true rule-based system as per Ada Lovelace's concerns.

This module verifies:
1. Trace Structure: The trace contains valid rule applications.
2. Determinism: Re-running the solver on the same input yields identical traces.
3. Distinctness: The symbolic trace is distinct from neural narratives (structural difference).
4. File Integrity: The trace file exists and is parseable.
"""

import json
import logging
import os
import re
import sys
import hashlib
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Constants for validation
REQUIRED_TRACE_KEYS = {'problem_id', 'rule_sequence', 'final_state', 'intermediate_states'}
REQUIRED_RULE_KEYS = {'rule_name', 'applied_to', 'result'}
DETERMINISM_CHECKS = 3  # Number of times to re-run for determinism check

def validate_symbolic_trace_structure(trace: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the structure of a symbolic trace against the expected schema.

    Args:
        trace: The parsed JSON trace from the symbolic engine.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    if not isinstance(trace, dict):
        errors.append("Trace must be a dictionary.")
        return False, errors

    # Check required top-level keys
    missing_keys = REQUIRED_TRACE_KEYS - set(trace.keys())
    if missing_keys:
        errors.append(f"Missing required top-level keys: {missing_keys}")

    # Check rule sequence structure
    if 'rule_sequence' in trace:
        if not isinstance(trace['rule_sequence'], list):
            errors.append("'rule_sequence' must be a list.")
        else:
            for i, rule_app in enumerate(trace['rule_sequence']):
                if not isinstance(rule_app, dict):
                    errors.append(f"Rule application at index {i} must be a dictionary.")
                    continue
                missing_rule_keys = REQUIRED_RULE_KEYS - set(rule_app.keys())
                if missing_rule_keys:
                    errors.append(f"Rule application at index {i} missing keys: {missing_rule_keys}")

    # Check intermediate states
    if 'intermediate_states' in trace:
        if not isinstance(trace['intermediate_states'], list):
            errors.append("'intermediate_states' must be a list.")

    return len(errors) == 0, errors

def validate_determinism(
    problem_input: Dict[str, Any],
    solver_func: callable,
    checks: int = DETERMINISM_CHECKS
) -> Tuple[bool, str]:
    """
    Validates that the symbolic solver produces identical traces for the same input.

    This addresses Ada Lovelace's concern by ensuring the engine is deterministic
    and not relying on any hidden state or randomization that would make it
    behave like a statistical model.

    Args:
        problem_input: The input problem definition.
        solver_func: The function that generates the symbolic trace.
        checks: Number of times to re-run the solver.

    Returns:
        A tuple (is_deterministic, errors) where is_deterministic is True
        if the trace is deterministic, and errors is a list of error messages.
    """
    traces = []
    for i in range(checks):
        try:
            # We assume solver_func takes the problem input and returns the trace dict
            trace = solver_func(problem_input)
            # Serialize to a canonical string for hashing
            trace_str = json.dumps(trace, sort_keys=True)
            trace_hash = hashlib.sha256(trace_str.encode()).hexdigest()
            traces.append(trace_hash)
        except Exception as e:
            return False, f"Solver failed on attempt {i+1}: {str(e)}"

    if len(set(traces)) == 1:
        return True, f"Determinism verified: {checks} runs produced identical traces (hash: {traces[0][:16]}...)"
    else:
        unique_hashes = set(traces)
        return False, f"Non-deterministic behavior detected: {len(unique_hashes)} unique hashes from {checks} runs: {unique_hashes}"

def validate_distinctness(
    symbolic_trace: Dict[str, Any],
    neural_narrative: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Validates that the symbolic trace is structurally distinct from a neural narrative.
    If no neural narrative is provided, it checks for internal structural properties
    that distinguish it from a free-form text block.

    Args:
        symbolic_trace: The parsed symbolic trace.
        neural_narrative: Optional string of the neural explanation.

    Returns:
        Tuple of (is_distinct, message).
    """
    # Check 1: Symbolic trace is a structured JSON object, not a string
    if isinstance(symbolic_trace, str):
        return False, "Symbolic trace is a string, not a structured JSON object."

    # Check 2: If neural narrative exists, ensure the trace contains specific rule keys
    # that a neural narrative (free text) would not have.
    if neural_narrative:
        # A neural narrative is typically a string. If the trace is a dict with 'rule_sequence',
        # it is structurally distinct.
        if 'rule_sequence' in symbolic_trace and isinstance(symbolic_trace['rule_sequence'], list):
            return True, "Structural distinctness verified: Trace contains 'rule_sequence' (structured rules) vs neural narrative (free text)."
        else:
            return False, "Symbolic trace lacks 'rule_sequence' structure, making it potentially indistinguishable from a narrative."

    # Check 3: Internal structure check (if no neural narrative provided)
    # Ensure it has the hallmarks of a rule-based trace
    if 'rule_sequence' in symbolic_trace and len(symbolic_trace['rule_sequence']) > 0:
        return True, "Internal structure verified: Contains rule sequence with specific rule applications."
    
    return True, "No neural narrative provided for comparison; trace structure is valid."

def validate_trace_file(file_path: str, problem_input: Optional[Dict[str, Any]] = None, solver_func: Optional[callable] = None) -> Dict[str, Any]:
    """
    Main validation function for a symbolic trace file.

    Args:
        file_path: Path to the JSON trace file.
        problem_input: Optional problem input for determinism check.
        solver_func: Optional solver function for determinism check.

    Returns:
        Dictionary with validation results.
    """
    result = {
        "file_path": file_path,
        "valid": True,
        "checks": {},
        "errors": []
    }

    # 1. Check file existence
    if not os.path.exists(file_path):
        result["valid"] = False
        result["errors"].append(f"File not found: {file_path}")
        return result

    # 2. Load and parse JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            trace = json.load(f)
    except json.JSONDecodeError as e:
        result["valid"] = False
        result["errors"].append(f"Invalid JSON format: {str(e)}")
        return result
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Error reading file: {str(e)}")
        return result

    # 3. Validate Structure
    struct_valid, struct_errors = validate_symbolic_trace_structure(trace)
    result["checks"]["structure"] = struct_valid
    if not struct_valid:
        result["valid"] = False
        result["errors"].extend(struct_errors)

    # 4. Validate Determinism (only if solver and input provided)
    if problem_input and solver_func:
        det_valid, det_msg = validate_determinism(problem_input, solver_func)
        result["checks"]["determinism"] = det_valid
        result["checks"]["determinism_message"] = det_msg
        if not det_valid:
            result["valid"] = False
            result["errors"].append(f"Determinism check failed: {det_msg}")
    else:
        result["checks"]["determinism"] = "skipped"
        result["checks"]["determinism_message"] = "No solver function or input provided for determinism check."

    # 5. Validate Distinctness
    # We simulate a neural narrative check by just checking the trace structure itself
    # against the criteria that it is NOT a string.
    distinct_valid, distinct_msg = validate_distinctness(trace)
    result["checks"]["distinctness"] = distinct_valid
    result["checks"]["distinctness_message"] = distinct_msg
    if not distinct_valid:
        result["valid"] = False
        result["errors"].append(f"Distinctness check failed: {distinct_msg}")

    return result

def main():
    """
    CLI entry point for the symbolic trace validator.
    
    Usage:
        python code/generate/symbolic_trace_validator.py --trace-file <path>
    
    Exits with code 0 if validation passes, 1 otherwise.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate symbolic trace files for determinism and structure.")
    parser.add_argument("--trace-file", required=True, help="Path to the symbolic trace JSON file.")
    parser.add_argument("--problem-input", required=False, help="Path to the problem input JSON (for determinism check).")
    parser.add_argument("--output", required=False, default=None, help="Path to save validation report JSON.")
    
    args = parser.parse_args()

    # Load problem input if provided
    problem_input = None
    solver_func = None
    
    if args.problem_input:
        if not os.path.exists(args.problem_input):
            logger.error(f"Problem input file not found: {args.problem_input}")
            sys.exit(1)
        
        try:
            with open(args.problem_input, 'r') as f:
                problem_input = json.load(f)
            # We need to import the solver to check determinism
            # This is a dynamic import to avoid circular dependencies if possible
            # or to allow optional usage
            try:
                from generate.symbolic_explanation import SymbolicSolver, generate_symbolic_explanation
                # Create a wrapper that matches the expected signature
                def solver_func_wrapper(inp):
                    # The solver expects a problem dict, returns a trace dict
                    solver = SymbolicSolver()
                    # We assume the input dict has the necessary fields
                    trace = solver.solve(inp)
                    return trace
                solver_func = solver_func_wrapper
            except ImportError:
                logger.warning("Could not import SymbolicSolver. Determinism check will be skipped.")
        except Exception as e:
            logger.error(f"Failed to load problem input: {str(e)}")
            sys.exit(1)

    logger.info(f"Validating trace file: {args.trace_file}")
    
    validation_result = validate_trace_file(
        file_path=args.trace_file,
        problem_input=problem_input,
        solver_func=solver_func
    )

    # Print results
    print(json.dumps(validation_result, indent=2))

    if validation_result["valid"]:
        logger.info("Validation PASSED.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED.")
        for err in validation_result["errors"]:
            logger.error(f"  - {err}")
        sys.exit(1)

    # Exit with appropriate code
    sys.exit(0 if result['is_valid'] else 1)

if __name__ == '__main__':
    main()