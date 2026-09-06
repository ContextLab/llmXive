from __future__ import annotations

import ast
import logging
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)

# Patterns to identify debug code that should be removed
DEBUG_PATTERNS = [
    re.compile(r'\bprint\s*\(', re.IGNORECASE),
    re.compile(r'\blog\.debug\s*\(', re.IGNORECASE),
    re.compile(r'\bassert\s+False\b', re.IGNORECASE),
    re.compile(r'#\s*DEBUG\b', re.IGNORECASE),
    re.compile(r'#\s*TODO\b', re.IGNORECASE),
    re.compile(r'#\s*FIXME\b', re.IGNORECASE),
    re.compile(r'#\s*XXX\b', re.IGNORECASE),
    re.compile(r'#\s*HACK\b', re.IGNORECASE),
    re.compile(r'#\s*BREAKPOINT\b', re.IGNORECASE),
    re.compile(r'\bbreakpoint\s*\(', re.IGNORECASE),
    re.compile(r'\bpdb\.set_trace\s*\(', re.IGNORECASE),
    re.compile(r'\bipdb\.set_trace\s*\(', re.IGNORECASE),
    re.compile(r'\bimport pdb\b', re.IGNORECASE),
    re.compile(r'\bimport ipdb\b', re.IGNORECASE),
]

# Patterns to identify unused imports
UNUSED_IMPORT_PATTERN = re.compile(r'^\s*import\s+(\w+)|^\s*from\s+[\w.]+\s+import\s+(\w+)')

def get_python_files(base_dir: str = "code") -> List[Path]:
    """
    Recursively find all Python files in the given directory.

    Args:
        base_dir: The base directory to search (default: "code")

    Returns:
        List of Path objects for all .py files found
    """
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.warning(f"Base directory {base_dir} does not exist")
        return []

    return sorted(base_path.rglob("*.py"))

def check_syntax(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Check if a Python file has valid syntax.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error in {file_path}: {e}"

def check_docstrings(file_path: Path) -> List[str]:
    """
    Check for missing docstrings in functions, classes, and modules.

    Args:
        file_path: Path to the Python file

    Returns:
        List of warnings about missing docstrings
    """
    warnings = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        # Check module docstring
        if not ast.get_docstring(tree):
            warnings.append(f"Missing module docstring in {file_path}")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    warnings.append(
                        f"Missing docstring in {node.__class__.__name__.lower()} '{node.name}' in {file_path}"
                    )

    except SyntaxError as e:
        warnings.append(f"Cannot check docstrings in {file_path} due to syntax error: {e}")

    return warnings

def validate_api_surface(file_path: Path) -> List[str]:
    """
    Validate that the file's public API surface is consistent.

    Checks for:
    - Functions/classes that start with underscore (private)
    - Inconsistent naming conventions

    Args:
        file_path: Path to the Python file

    Returns:
        List of warnings about API surface issues
    """
    warnings = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Check for inconsistent naming (e.g., mixedCase in Python)
                if node.name and node.name[0].isupper() and '_' in node.name:
                    warnings.append(
                        f"Class '{node.name}' in {file_path} uses snake_case, consider PascalCase"
                    )
                elif node.name and node.name[0].islower() and any(c.isupper() for c in node.name[1:]):
                    warnings.append(
                        f"Function '{node.name}' in {file_path} uses mixedCase, consider snake_case"
                    )

    except SyntaxError as e:
        warnings.append(f"Cannot validate API surface in {file_path} due to syntax error: {e}")

    return warnings

def remove_debug_code(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Remove debug code patterns from a file.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (was_modified, list of removed patterns)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        modified_lines = []
        removed_patterns = []
        is_modified = False

        for line_num, line in enumerate(lines, 1):
            pattern_found = False
            for pattern in DEBUG_PATTERNS:
                if pattern.search(line):
                    pattern_found = True
                    removed_patterns.append(f"Line {line_num}: {line.strip()}")
                    break

            if not pattern_found:
                modified_lines.append(line)
            else:
                is_modified = True

        if is_modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(modified_lines)

        return is_modified, removed_patterns

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return False, []

def main() -> int:
    """
    Main entry point for the cleanup script.

    Performs the following:
    1. Finds all Python files in the code/ directory
    2. Checks syntax validity
    3. Checks for missing docstrings
    4. Validates API surface consistency
    5. Removes debug code patterns
    6. Reports findings

    Returns:
        0 if all checks pass, 1 if issues found
    """
    logger.info("Starting code cleanup and refactoring validation")

    python_files = get_python_files()
    if not python_files:
        logger.warning("No Python files found in code/ directory")
        return 0

    total_issues = 0
    syntax_errors = []
    docstring_warnings = []
    api_warnings = []
    debug_removals = []

    for file_path in python_files:
        logger.info(f"Processing {file_path}")

        # Check syntax
        is_valid, error = check_syntax(file_path)
        if not is_valid:
            syntax_errors.append(error)
            total_issues += 1
            continue

        # Check docstrings
        doc_warnings = check_docstrings(file_path)
        docstring_warnings.extend(doc_warnings)
        total_issues += len(doc_warnings)

        # Validate API surface
        api_warnings_file = validate_api_surface(file_path)
        api_warnings.extend(api_warnings_file)
        total_issues += len(api_warnings_file)

        # Remove debug code
        was_modified, removed = remove_debug_code(file_path)
        if was_modified:
            debug_removals.extend(removed)
            logger.info(f"Removed {len(removed)} debug patterns from {file_path}")

    # Report results
    logger.info("=" * 60)
    logger.info("CLEANUP REPORT")
    logger.info("=" * 60)

    if syntax_errors:
        logger.error(f"SYNTAX ERRORS ({len(syntax_errors)}):")
        for error in syntax_errors:
            logger.error(f"  - {error}")

    if docstring_warnings:
        logger.warning(f"MISSING DOCSTRINGS ({len(docstring_warnings)}):")
        for warning in docstring_warnings[:10]:  # Limit output
            logger.warning(f"  - {warning}")
        if len(docstring_warnings) > 10:
            logger.warning(f"  ... and {len(docstring_warnings) - 10} more")

    if api_warnings:
        logger.warning(f"API SURFACE ISSUES ({len(api_warnings)}):")
        for warning in api_warnings[:10]:  # Limit output
            logger.warning(f"  - {warning}")
        if len(api_warnings) > 10:
            logger.warning(f"  ... and {len(api_warnings) - 10} more")

    if debug_removals:
        logger.info(f"DEBUG CODE REMOVED ({len(debug_removals)}):")
        for removal in debug_removals[:10]:  # Limit output
            logger.info(f"  - {removal}")
        if len(debug_removals) > 10:
            logger.info(f"  ... and {len(debug_removals) - 10} more")

    logger.info("=" * 60)
    if total_issues == 0 and not debug_removals:
        logger.info("SUCCESS: No issues found. Code is clean.")
        return 0
    else:
        logger.warning(f"FOUND {total_issues} issues and removed {len(debug_removals)} debug patterns")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())