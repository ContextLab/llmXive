"""
Constitution Enforcement Tests for Project PROJ-925.

This module implements static analysis checks to ensure:
1. No forbidden imports (PIL, opencv, torch.cuda, tensorflow) in code/features.py.
2. No CUDA usage in code/data/train.py.
3. CPU-only constraints are met (torch.set_num_threads, etc.).

These tests act as a gate for T014b (validation of T014a) and T029b.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Set

import pytest

# Add project root to path if running from tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"


class ConstitutionError(Exception):
    """Raised when a constitutional rule is violated."""
    pass


def get_file_source(file_path: Path) -> str:
    """Reads the source code of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def parse_source(source: str) -> ast.AST:
    """Parses Python source code into an AST."""
    try:
        return ast.parse(source)
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in source: {e}")


def check_forbidden_imports_in_file(file_path: Path, forbidden_modules: Set[str]) -> List[str]:
    """
    Static analysis to check for forbidden imports in a specific file.
    
    Args:
        file_path: Path to the Python file to check.
        forbidden_modules: Set of module names that are forbidden (e.g., 'PIL', 'cv2', 'torch.cuda').
        
    Returns:
        List of violation messages.
    """
    source = get_file_source(file_path)
    tree = parse_source(source)
    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Check exact match or top-level match
                module_name = alias.name.split('.')[0]
                if module_name in forbidden_modules or alias.name in forbidden_modules:
                    violations.append(
                        f"Forbidden import '{alias.name}' found in {file_path.name} at line {node.lineno}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                # Special handling for torch.cuda
                if node.module == "torch.cuda":
                    violations.append(
                        f"Forbidden import 'from torch.cuda' found in {file_path.name} at line {node.lineno}"
                    )
                elif module_name in forbidden_modules or node.module in forbidden_modules:
                    violations.append(
                        f"Forbidden import 'from {node.module}' found in {file_path.name} at line {node.lineno}"
                    )
            else:
                # Handle relative imports if necessary, though usually forbidden modules are absolute
                for alias in node.names:
                    if alias.name in forbidden_modules:
                        violations.append(
                            f"Forbidden import 'from . import {alias.name}' found in {file_path.name} at line {node.lineno}"
                        )
    
    return violations


def check_cpu_constraints_in_train(file_path: Path) -> List[str]:
    """
    Static analysis to verify CPU-only constraints in code/data/train.py.
    
    Checks:
    1. No 'torch.cuda' usage.
    2. Presence of 'torch.set_num_threads(1)' and 'torch.set_num_interop_threads(1)'.
    
    Args:
        file_path: Path to code/data/train.py.
        
    Returns:
        List of violation messages.
    """
    source = get_file_source(file_path)
    tree = parse_source(source)
    violations = []
    
    has_set_num_threads = False
    has_set_num_interop_threads = False
    
    # Check for forbidden CUDA imports/usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("torch.cuda"):
                    violations.append(
                        f"Forbidden import 'torch.cuda' found in {file_path.name} at line {node.lineno}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("torch.cuda"):
                violations.append(
                    f"Forbidden import 'from torch.cuda' found in {file_path.name} at line {node.lineno}"
                )
        
        # Check for function calls that set CPU constraints
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "torch":
                    if node.func.attr == "set_num_threads":
                        has_set_num_threads = True
                    elif node.func.attr == "set_num_interop_threads":
                        has_set_num_interop_threads = True
                
                # Check for .cuda() calls on tensors/models
                if node.func.attr == "cuda":
                    violations.append(
                        f"Forbidden .cuda() call found in {file_path.name} at line {node.lineno}"
                    )

    if not has_set_num_threads:
        violations.append(
            "Missing 'torch.set_num_threads(1)' call in code/data/train.py. "
            "This is required to enforce CPU-only execution."
        )
    
    if not has_set_num_interop_threads:
        violations.append(
            "Missing 'torch.set_num_interop_threads(1)' call in code/data/data/train.py. "
            "This is required to enforce CPU-only execution."
        )

    return violations


class TestConstitution:
    """Test suite for Constitution Enforcement rules."""

    def test_no_forbidden_imports_in_features(self):
        """
        T043: Scan code/features.py for forbidden imports (PIL, opencv, torch.cuda, tensorflow).
        If found, raise ImportError.
        """
        features_path = CODE_DIR / "features.py"
        if not features_path.exists():
            pytest.skip("code/features.py not found (task not implemented yet)")

        forbidden = {"PIL", "cv2", "torch.cuda", "tensorflow", "keras"}
        violations = check_forbidden_imports_in_file(features_path, forbidden)

        if violations:
            error_msg = "Constitution Violation in code/features.py:\n" + "\n".join(violations)
            raise ImportError(error_msg)

    def test_cpu_constraints_in_train(self):
        """
        T044: Scan code/data/train.py for CUDA usage and verify CPU constraints.
        Explicitly verify torch.set_num_threads(1) and torch.set_num_interop_threads(1).
        Raise ImportError if torch.cuda is imported or constraints missing.
        """
        train_path = CODE_DIR / "data" / "train.py"
        if not train_path.exists():
            pytest.skip("code/data/train.py not found (task not implemented yet)")

        violations = check_cpu_constraints_in_train(train_path)

        if violations:
            error_msg = "Constitution Violation in code/data/train.py:\n" + "\n".join(violations)
            raise ImportError(error_msg)

    def test_no_gpu_leakage_in_features(self):
        """
        Additional check: Ensure no GPU device placement in code/features.py.
        """
        features_path = CODE_DIR / "features.py"
        if not features_path.exists():
            pytest.skip("code/features.py not found")

        source = get_file_source(features_path)
        if ".to('cuda')" in source or ".to('gpu')" in source:
            raise ImportError("Constitution Violation: GPU device placement found in code/features.py")
        
        # Check for explicit device assignment
        if "device = 'cuda'" in source or "device = torch.device('cuda')" in source:
            raise ImportError("Constitution Violation: CUDA device assignment found in code/features.py")

def run_constitution_checks():
    """
    Helper function to run checks manually (e.g., from a script).
    Returns True if all checks pass, False otherwise.
    """
    try:
        test_suite = TestConstitution()
        test_suite.test_no_forbidden_imports_in_features()
        test_suite.test_cpu_constraints_in_train()
        test_suite.test_no_gpu_leakage_in_features()
        print("Constitution checks PASSED.")
        return True
    except ImportError as e:
        print(f"Constitution checks FAILED: {e}")
        return False
    except FileNotFoundError as e:
        print(f"File missing: {e}")
        return False

if __name__ == "__main__":
    success = run_constitution_checks()
    sys.exit(0 if success else 1)
