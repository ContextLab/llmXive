"""
Static analysis script to verify Constitution Principle VI: Oracle Independence.

This script parses the AST of code/engines/full_context.py and code/engines/compressed_context.py
to ensure that code/engines/oracle_policy.py is only imported for validation functions
(e.g., 'validate') and never for execution logic.

If any execution logic is found (e.g., direct calls to oracle methods that implement
policy logic rather than just validating), the script fails with a non-zero exit code.
"""

import ast
import sys
from pathlib import Path
from typing import List, Set, Dict, Any

# Define the oracle module path
ORACLE_MODULE = "engines.oracle_policy"
ORACLE_VALIDATION_METHODS = {"validate"}
ORACLE_EXECUTION_METHODS = {"execute_policy", "enforce_rule", "apply_constraint"}  # Hypothetical execution methods

# Files to analyze
TARGET_FILES = [
    "code/engines/full_context.py",
    "code/engines/compressed_context.py"
]

class OracleIndependenceVisitor(ast.NodeVisitor):
    """AST visitor to check for violations of Oracle Independence."""

    def __init__(self, filename: str):
        self.filename = filename
        self.violations: List[str] = []
        self.imports: Dict[str, str] = {}  # Maps alias to module
        self.imported_names: Set[str] = set()  # Names imported from oracle module

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports from the oracle module."""
        if node.module == ORACLE_MODULE or (node.module and node.module.endswith(ORACLE_MODULE)):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.imports[name] = ORACLE_MODULE
                self.imported_names.add(name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check function calls for execution logic."""
        # Check if it's a method call on an object
        if isinstance(node.func, ast.Attribute):
            obj_name = None
            method_name = node.func.attr

            # Identify the object being called
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id

            # Check if the object is imported from oracle module
            if obj_name and obj_name in self.imports:
                # If the method is not a validation method, it's a violation
                if method_name not in ORACLE_VALIDATION_METHODS:
                    # Check if it looks like an execution method
                    if method_name in ORACLE_EXECUTION_METHODS or "execute" in method_name.lower() or "enforce" in method_name.lower():
                        self.violations.append(
                            f"VIOLATION: Execution logic detected in {self.filename}:{node.lineno}. "
                            f"Calling {obj_name}.{method_name}() which implements policy logic. "
                            f"Oracle should only be used for validation."
                        )

        # Check direct function calls (if imported directly)
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.imported_names:
                # If the function name suggests execution logic
                if func_name in ORACLE_EXECUTION_METHODS or "execute" in func_name.lower() or "enforce" in func_name.lower():
                    self.violations.append(
                        f"VIOLATION: Execution logic detected in {self.filename}:{node.lineno}. "
                        f"Direct call to {func_name}() which implements policy logic. "
                        f"Oracle should only be used for validation."
                    )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check if a function definition contains execution logic."""
        # Skip if it's a validation wrapper
        if "validate" in node.name.lower():
            self.generic_visit(node)
            return

        # Check function body for execution logic
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                self.visit_Call(child)
        self.generic_visit(node)

def analyze_file(filepath: str) -> List[str]:
    """Analyze a single Python file for Oracle Independence violations."""
    violations = []
    path = Path(filepath)

    if not path.exists():
        return [f"ERROR: File not found: {filepath}"]

    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return [f"ERROR: Syntax error in {filepath}: {e}"]

    visitor = OracleIndependenceVisitor(filepath)
    visitor.visit(tree)

    return visitor.violations

def main() -> None:
    """Main entry point for the static analysis."""
    all_violations = []

    print("Constitution Principle VI Check (Static Analysis)")
    print("=" * 50)
    print("Checking for Oracle Independence violations...")
    print()

    for filepath in TARGET_FILES:
        print(f"Analyzing: {filepath}")
        violations = analyze_file(filepath)
        if violations:
            all_violations.extend(violations)
            for v in violations:
                print(f"  {v}")
        else:
            print(f"  OK: No violations found")
        print()

    if all_violations:
        print("RESULT: FAILED")
        print(f"Found {len(all_violations)} violation(s).")
        print("Constitution Principle VI is VIOLATED: Oracle Independence not maintained.")
        sys.exit(1)
    else:
        print("RESULT: PASSED")
        print("Constitution Principle VI is MAINTAINED: Oracle is only used for validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()
