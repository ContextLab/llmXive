import ast
import sys
import os
from pathlib import Path
from typing import List, Set, Tuple

# Forbidden names that indicate leakage of internal model details into the evaluation pipeline
FORBIDDEN_NAMES = {
    "dit_attention",
    "latent_space",
    "attention_map",
    "diagonal_attention",
    "self_attention_weights",
    "cross_attention_weights",
    "model_backbone",
    "transformer_blocks",
    "hidden_states",
    "residuals",
    "embeddings",
}

def check_file_integrity(file_path: str, forbidden_names: Set[str] = None) -> Tuple[bool, List[str]]:
    """
    Perform static analysis on a Python file to ensure it does not import
    or reference forbidden internal model components.

    Args:
        file_path: Path to the Python file to check.
        forbidden_names: Set of names that are forbidden to be imported or used.

    Returns:
        Tuple of (is_valid, list_of_violations)
    """
    if forbidden_names is None:
        forbidden_names = FORBIDDEN_NAMES

    violations = []
    file_path = Path(file_path)

    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return False, [f"Syntax error in file: {e}"]

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name.split(".")[0]
                if name in forbidden_names:
                    violations.append(f"Forbidden import found: {name} (line {node.lineno})")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_parts = node.module.split(".")
                for part in module_parts:
                    if part in forbidden_names:
                        violations.append(f"Forbidden import from module found: {node.module} (line {node.lineno})")
            for alias in node.names:
                name = alias.name
                if name in forbidden_names:
                    violations.append(f"Forbidden import name found: {name} (line {node.lineno})")

    # Check for usage of forbidden names in expressions (simple heuristic)
    # Note: This is a basic check and might have false positives if variable names match
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in forbidden_names:
                # Check if it's not part of a string or comment (AST doesn't capture comments easily)
                # We'll assume if it's a Name node, it's likely a reference
                violations.append(f"Forbidden name usage found: {node.id} (line {node.lineno})")
        elif isinstance(node, ast.Attribute):
            # Check for attribute access like module.forbidden_name
            if isinstance(node.attr, str) and node.attr in forbidden_names:
                violations.append(f"Forbidden attribute access found: {node.attr} (line {node.lineno})")

    is_valid = len(violations) == 0
    return is_valid, violations

def main():
    """
    Main entry point for the static analysis check.
    Checks code/pipeline/evaluate.py for forbidden imports.
    """
    project_root = Path(__file__).parent.parent.parent
    evaluate_file = project_root / "code" / "pipeline" / "evaluate.py"

    print(f"Checking file: {evaluate_file}")

    if not evaluate_file.exists():
        print(f"ERROR: File not found: {evaluate_file}")
        sys.exit(1)

    is_valid, violations = check_file_integrity(str(evaluate_file))

    if is_valid:
        print("SUCCESS: No forbidden imports or references found.")
        sys.exit(0)
    else:
        print("FAILURE: Forbidden imports or references detected:")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)

if __name__ == "__main__":
    main()
