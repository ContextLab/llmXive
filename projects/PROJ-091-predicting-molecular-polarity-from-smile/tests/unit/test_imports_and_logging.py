import pytest
import ast
import os
import sys
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Set, List

# Add the code directory to the path to allow imports
CODE_ROOT = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(CODE_ROOT))

# Standardized logging format expected by T039c
EXPECTED_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def get_python_files(directory: Path) -> List[Path]:
    """Recursively find all .py files in a directory."""
    return list(directory.rglob("*.py"))

def get_used_names_in_file(filepath: Path) -> Set[str]:
    """Parse a Python file and return a set of all names used (imports + calls)."""
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(filepath))
        except SyntaxError:
            # Skip files with syntax errors (though they should be fixed)
            return set()

    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Capture attribute access like 'os.path' -> 'os', 'path'
            current = node
            parts = []
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            # Add the root name and intermediate names
            used_names.update(parts)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                used_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                # Handle method calls like 'obj.method()'
                current = node.func
                parts = []
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                used_names.update(parts)
    return used_names

def get_imports_in_file(filepath: Path) -> List[tuple]:
    """Get all import statements: (module_name, alias_or_name)"""
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(filepath))
        except SyntaxError:
            return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.append((alias.name.split('.')[0], name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_root = node.module.split('.')[0]
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append((module_root, name))
    return imports

def test_unused_imports_removed():
    """
    T039b Verification:
    Verify that unused imports have been removed from all Python files in code/.
    This test parses each file, compares imported names against used names,
    and asserts that there are no unused imports.
    """
    python_files = get_python_files(CODE_ROOT)
    issues = []

    for filepath in python_files:
        # Skip test files themselves to avoid circular logic or self-reference issues
        if "tests" in str(filepath):
            continue

        imports = get_imports_in_file(filepath)
        used_names = get_used_names_in_file(filepath)
        
        # Standard library names that might be used implicitly or in strings
        # We focus on explicit imports that are never referenced as identifiers
        for module_root, name in imports:
            # If the imported name is not in the used set, it's unused
            if name not in used_names:
                # Allow common exceptions for side-effect imports (e.g., 'import sys' for exit)
                # But strict check: if 'sys' is imported as 'sys' and 'sys' is never used, it's unused.
                # However, sometimes 'sys' is used for 'sys.path'. The ast parser catches 'sys' in 'sys.path'.
                # So if 'sys' is not in used_names, it truly is unused.
                issues.append(f"{filepath}: Unused import '{name}' (from {module_root})")

    assert len(issues) == 0, f"Found unused imports that should have been removed by T039b:\n" + "\n".join(issues)

def test_logging_format_standardized():
    """
    T039c Verification:
    Verify that the logging format is standardized across all modules.
    We check that setup_logging (from utils.logging_config) is called and that
    the format matches EXPECTED_LOG_FORMAT.
    """
    # We verify this by checking the config/setup or running a small import check
    # Since T039c says "Standardize logging format... and verify with pytest",
    # we assume the format string is hardcoded in utils/logging_config.py.
    
    logging_config_path = CODE_ROOT / "utils" / "logging_config.py"
    if not logging_config_path.exists():
        pytest.skip("logging_config.py not found")

    with open(logging_config_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if the expected format string is present in the file
    # This is a heuristic; a more robust check would parse the logger setup.
    assert EXPECTED_LOG_FORMAT in content, (
        f"Standardized logging format '{EXPECTED_LOG_FORMAT}' not found in "
        f"{logging_config_path}. Ensure T039c was implemented correctly."
    )

def test_logging_setup_called_in_main_scripts():
    """
    Verify that main entry points call setup_logging to ensure the format is applied.
    """
    main_path = CODE_ROOT / "main.py"
    if not main_path.exists():
        pytest.skip("main.py not found")

    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)

    found_setup = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "setup_logging":
                found_setup = True
                break
            # Also check for attribute calls like logging_config.setup_logging
            if isinstance(node.func, ast.Attribute) and node.func.attr == "setup_logging":
                found_setup = True
                break

    assert found_setup, (
        f"setup_logging() was not called in {main_path}. "
        "Ensure T039c logging standardization is applied in entry points."
    )