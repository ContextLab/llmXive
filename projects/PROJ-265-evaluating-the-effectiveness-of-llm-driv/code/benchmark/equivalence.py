"""
Functional equivalence check logic for LLM-driven code simplification.

Implements AST-based structural diffing and type-aware random input execution
to verify that simplified code produces identical outputs to the original code.

This module satisfies FR-006 (Equivalence Check), FR-007 (Drift Detection),
and FR-012 (Drift Logging).
"""

import ast
import random
import sys
import tempfile
import traceback
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path

# Import sandbox utilities from existing project structure
# Note: We assume utils.sandbox is available as per existing API surface
# If run as standalone script, we might need to adjust imports, but per spec
# we use the existing API surface.
try:
    from utils.sandbox import run_in_sandbox, ExecutionResult, SandboxTimeoutError, SandboxMemoryError
except ImportError:
    # Fallback for direct execution if path isn't set up correctly
    # In a real run, utils.sandbox should be importable
    from code.utils.sandbox import run_in_sandbox, ExecutionResult, SandboxTimeoutError, SandboxMemoryError


@dataclass
class DriftLog:
    """Structured log of equivalence check results and drift reasons."""
    is_equivalent: bool
    original_code: str
    simplified_code: str
    drift_reasons: List[str] = field(default_factory=list)
    execution_errors: List[Dict[str, Any]] = field(default_factory=list)
    input_tests: List[Dict[str, Any]] = field(default_factory=list)
    ast_diff_summary: Optional[str] = None

def normalize_ast(node: ast.AST) -> ast.AST:
    """
    Normalize AST by removing irrelevant nodes (e.g., comments, specific line numbers)
    to focus on structural equivalence.
    """
    # Create a copy and strip irrelevant attributes
    # This is a simplified normalization; a full implementation would be more complex
    if isinstance(node, ast.AST):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                new_list = []
                for item in value:
                    if isinstance(item, ast.AST):
                        new_list.append(normalize_ast(item))
                    else:
                        new_list.append(item)
                setattr(node, field, new_list)
            elif isinstance(value, ast.AST):
                setattr(node, field, normalize_ast(value))
            # Remove line numbers and column offsets which vary by formatting
            if hasattr(node, 'lineno'):
                delattr(node, 'lineno')
            if hasattr(node, 'col_offset'):
                delattr(node, 'col_offset')
            if hasattr(node, 'end_lineno'):
                delattr(node, 'end_lineno')
            if hasattr(node, 'end_col_offset'):
                delattr(node, 'end_col_offset')
    return node


def get_ast_diff_summary(original: ast.AST, simplified: ast.AST) -> str:
    """
    Generate a human-readable summary of AST differences.
    Returns a string describing structural differences.
    """
    original_normalized = normalize_ast(original)
    simplified_normalized = normalize_ast(simplified)

    # Simple comparison: if normalized ASTs are identical, no drift
    if ast.dump(original_normalized) == ast.dump(simplified_normalized):
        return "AST structures are identical after normalization"

    # If different, provide a basic diff description
    # In a more advanced implementation, we could use astor or similar for better diffs
    return f"AST difference detected: Original has {len(ast.walk(original))} nodes, Simplified has {len(ast.walk(simplified))} nodes"


def extract_function_signature(code: str) -> Optional[ast.FunctionDef]:
    """
    Extract the main function definition from code.
    Assumes the code contains exactly one top-level function or the first one is the target.
    """
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node
        return None
    except SyntaxError:
        return None


def generate_type_aware_inputs(func_node: ast.FunctionDef, max_tests: int = 5) -> List[Dict[str, Any]]:
    """
    Generate random inputs based on the function's type hints.
    If no type hints are present, generates generic inputs.
    """
    inputs_list = []

    # Get argument names
    args = func_node.args
    arg_names = [arg.arg for arg in args.args]
    arg_types = [arg.annotation for arg in args.args]

    for i in range(max_tests):
        test_input = {}
        for j, name in enumerate(arg_names):
            if j < len(arg_types) and arg_types[j]:
                # Try to infer type from annotation
                ann = arg_types[j]
                if isinstance(ann, ast.Name):
                    type_name = ann.id
                    if type_name == 'int':
                        test_input[name] = random.randint(-100, 100)
                    elif type_name == 'float':
                        test_input[name] = random.uniform(-100.0, 100.0)
                    elif type_name == 'str':
                        test_input[name] = f"test_string_{random.randint(0, 100)}"
                    elif type_name == 'bool':
                        test_input[name] = random.choice([True, False])
                    elif type_name == 'list':
                        test_input[name] = [random.randint(0, 10) for _ in range(3)]
                    elif type_name == 'dict':
                        test_input[name] = {f"key_{k}": random.randint(0, 10) for k in range(3)}
                    else:
                        # Default fallback
                        test_input[name] = f"arg_{i}_{j}"
                else:
                    # Complex type, default to simple value
                    test_input[name] = f"arg_{i}_{j}"
            else:
                # No type hint, generate a generic value
                test_input[name] = f"arg_{i}_{j}"

        inputs_list.append(test_input)

    return inputs_list


def execute_function_with_inputs(code: str, func_name: str, inputs: Dict[str, Any], timeout: float = 5.0) -> Tuple[Optional[Any], Optional[str]]:
    """
    Execute the function with given inputs in a sandboxed environment.
    Returns (result, error_message).
    """
    # Prepare the execution code
    execution_code = f"""
{code}
result = {func_name}(**{inputs})
print(result)
"""

    try:
        result = run_in_sandbox(
            code=execution_code,
            timeout_seconds=timeout,
            memory_mb=500
        )
        if result.success:
            # Parse the output
            output = result.output.strip()
            try:
                # Try to eval the output to get the actual Python object
                # This is safe because we control the execution environment
                parsed_result = ast.literal_eval(output)
                return parsed_result, None
            except (ValueError, SyntaxError):
                # If literal_eval fails, return the string output
                return output, None
        else:
            error_msg = f"Execution failed: {result.error}"
            if hasattr(result, 'timeout') and result.timeout:
                error_msg += " (Timeout)"
            if hasattr(result, 'memory_limit') and result.memory_limit:
                error_msg += " (Memory limit)"
            return None, error_msg

    except Exception as e:
        return None, f"Execution error: {str(e)}"


def check_function_equivalence(
    original_code: str,
    simplified_code: str,
    random_inputs: Optional[List[Dict[str, Any]]] = None,
    num_random_tests: int = 5,
    timeout: float = 5.0
) -> Tuple[bool, DriftLog]:
    """
    Check if original_code and simplified_code are functionally equivalent.

    Args:
        original_code: The original Python function code.
        simplified_code: The simplified Python function code.
        random_inputs: Pre-generated random inputs (optional). If None, generated automatically.
        num_random_tests: Number of random input tests to run.
        timeout: Timeout in seconds for each execution.

    Returns:
        Tuple of (is_equivalent: bool, drift_log: DriftLog)
    """
    drift_log = DriftLog(
        is_equivalent=True,
        original_code=original_code,
        simplified_code=simplified_code
    )

    # Step 1: Parse both codes to verify syntax
    try:
        original_tree = ast.parse(original_code)
    except SyntaxError as e:
        drift_log.is_equivalent = False
        drift_log.drift_reasons.append(f"Original code syntax error: {str(e)}")
        return False, drift_log

    try:
        simplified_tree = ast.parse(simplified_code)
    except SyntaxError as e:
        drift_log.is_equivalent = False
        drift_log.drift_reasons.append(f"Simplified code syntax error: {str(e)}")
        return False, drift_log

    # Step 2: Extract function names
    original_func = extract_function_signature(original_code)
    simplified_func = extract_function_signature(simplified_code)

    if not original_func:
        drift_log.is_equivalent = False
        drift_log.drift_reasons.append("Could not extract function from original code")
        return False, drift_log

    if not simplified_func:
        drift_log.is_equivalent = False
        drift_log.drift_reasons.append("Could not extract function from simplified code")
        return False, drift_log

    # Use the original function name for execution
    func_name = original_func.name

    # Step 3: Generate or use provided random inputs
    if random_inputs is None:
        random_inputs = generate_type_aware_inputs(original_func, num_random_tests)

    # Step 4: Execute both functions with each input set
    for i, inputs in enumerate(random_inputs):
        # Execute original
        orig_result, orig_error = execute_function_with_inputs(
            original_code, func_name, inputs, timeout
        )

        # Execute simplified
        simp_result, simp_error = execute_function_with_inputs(
            simplified_code, func_name, inputs, timeout
        )

        test_record = {
            "test_index": i,
            "inputs": inputs,
            "original_result": str(orig_result) if orig_result is not None else None,
            "simplified_result": str(simp_result) if simp_result is not None else None,
            "original_error": orig_error,
            "simplified_error": simp_error
        }
        drift_log.input_tests.append(test_record)

        # Check for errors
        if orig_error:
            drift_log.execution_errors.append({
                "test_index": i,
                "source": "original",
                "error": orig_error
            })
            # Don't mark as non-equivalent yet, just log the error
            # But if simplified also has error, they might be equivalent in failure
            if simp_error:
                # Both failed, could be equivalent failure
                pass
            else:
                # Original failed, simplified succeeded -> drift
                drift_log.is_equivalent = False
                drift_log.drift_reasons.append(f"Test {i}: Original failed with '{orig_error}', simplified succeeded")

        elif simp_error:
            drift_log.execution_errors.append({
                "test_index": i,
                "source": "simplified",
                "error": simp_error
            })
            drift_log.is_equivalent = False
            drift_log.drift_reasons.append(f"Test {i}: Simplified failed with '{simp_error}', original succeeded")

        # If both succeeded, compare results
        elif orig_result != simp_result:
            drift_log.is_equivalent = False
            drift_log.drift_reasons.append(
                f"Test {i}: Results differ - Original: {orig_result}, Simplified: {simp_result}"
            )

    # Step 5: AST-based structural check (optional but informative)
    ast_summary = get_ast_diff_summary(original_tree, simplified_tree)
    drift_log.ast_diff_summary = ast_summary

    # If AST structures are significantly different but execution results match,
    # we still consider them equivalent (functional equivalence is what matters)
    # But we log the structural difference for analysis

    return drift_log.is_equivalent, drift_log


def run_equivalence_check_batch(
    pairs: List[Tuple[str, str]],
    num_random_tests: int = 5,
    timeout: float = 5.0
) -> List[Tuple[bool, DriftLog]]:
    """
    Run equivalence checks on a batch of (original, simplified) code pairs.

    Args:
        pairs: List of tuples containing (original_code, simplified_code)
        num_random_tests: Number of random input tests per pair
        timeout: Timeout in seconds per execution

    Returns:
        List of (is_equivalent, drift_log) tuples for each pair
    """
    results = []
    for i, (orig, simp) in enumerate(pairs):
        is_eq, log = check_function_equivalence(
            orig, simp, num_random_tests=num_random_tests, timeout=timeout
        )
        results.append((is_eq, log))
    return results


def main():
    """
    Main function to demonstrate the equivalence check logic.
    This can be used for testing or as a CLI tool.
    """
    # Example usage
    original = """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""

    simplified = """
def add_numbers(a: int, b: int) -> int:
    # Simplified version
    return a + b
"""

    is_equiv, log = check_function_equivalence(original, simplified)

    print(f"Equivalence Check Result: {is_equiv}")
    print(f"Drift Reasons: {log.drift_reasons}")
    if log.ast_diff_summary:
        print(f"AST Diff Summary: {log.ast_diff_summary}")
    print(f"Number of test inputs: {len(log.input_tests)}")

    return is_equiv


if __name__ == "__main__":
    main()