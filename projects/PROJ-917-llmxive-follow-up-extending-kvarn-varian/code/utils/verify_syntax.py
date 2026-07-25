"""
Syntax Verification Script for llmXive Project.

This script verifies that all Python files in the project compile successfully
using python -m py_compile. It is designed to be run as:
    python code/utils/verify_syntax.py

It recursively scans the 'code/' directory for .py files and attempts to compile them.
Any compilation errors are logged, and the script exits with a non-zero status
if any errors are found.
"""

import os
import sys
import py_compile
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_python_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all .py files in the given directory.

    Args:
        root_dir: The root directory to search.

    Returns:
        A list of Path objects for all .py files found.
    """
    py_files = []
    for path in root_dir.rglob('*.py'):
        # Skip __pycache__ directories
        if '__pycache__' not in str(path):
            py_files.append(path)
    return sorted(py_files)

def verify_syntax(file_path: Path) -> Tuple[bool, str]:
    """
    Verify the syntax of a single Python file.

    Args:
        file_path: Path to the Python file.

    Returns:
        A tuple (success, message).
        success is True if compilation succeeds, False otherwise.
        message contains details about the result or error.
    """
    try:
        py_compile.compile(str(file_path), doraise=True)
        return True, f"OK: {file_path}"
    except py_compile.PyCompileError as e:
        return False, f"FAIL: {file_path} - {e}"

def main():
    """
    Main entry point for the syntax verification script.
    """
    # Determine the project root relative to this script's location
    # The script is expected to be at code/utils/verify_syntax.py
    # so the project root is two levels up.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    logger.info(f"Project root detected at: {project_root}")
    code_dir = project_root / 'code'

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)

    logger.info(f"Scanning for Python files in: {code_dir}")
    py_files = find_python_files(code_dir)

    if not py_files:
        logger.warning("No Python files found to verify.")
        sys.exit(0)

    logger.info(f"Found {len(py_files)} Python files to verify.")

    results = []
    errors = []

    for file_path in py_files:
        success, message = verify_syntax(file_path)
        results.append((success, message))
        if not success:
            errors.append(message)

    # Log summary
    passed = sum(1 for success, _ in results if success)
    failed = sum(1 for success, _ in results if not success)

    logger.info(f"Verification complete. Passed: {passed}, Failed: {failed}")

    if errors:
        logger.error("The following files have syntax errors:")
        for error in errors:
            logger.error(f"  {error}")
        sys.exit(1)
    else:
        logger.info("All Python files compiled successfully.")
        sys.exit(0)

if __name__ == '__main__':
    main()