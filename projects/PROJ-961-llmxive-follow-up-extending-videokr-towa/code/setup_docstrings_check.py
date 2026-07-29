"""
Docstring Validation Utility for llmXive Project.

This script validates that all Python scripts in the `code/` directory
contain proper docstrings for modules, classes, and public functions.
It uses the `ast` module to parse Python files and verify documentation
presence without executing the code.
"""
import ast
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determine the project root directory.

    Returns:
        Path: The absolute path to the project root (parent of 'code' directory).
    """
    current_file = Path(__file__).resolve()
    # Assume project root is the parent of the 'code' directory
    # If this script is in code/, go up one level
    if current_file.name == "setup_docstrings_check.py":
        return current_file.parent.parent
    return current_file.parent

def check_module_docstring(tree: ast.AST, filepath: Path) -> Optional[str]:
    """
    Check if the module has a docstring.

    Args:
        tree: The parsed AST of the Python file.
        filepath: The path to the file being checked.

    Returns:
        str: Error message if missing, None if present.
    """
    docstring = ast.get_docstring(tree)
    if not docstring:
        return f"Module missing docstring: {filepath}"
    return None

def check_function_docstrings(node: ast.FunctionDef, filepath: Path) -> List[str]:
    """
    Check if a function has a docstring.

    Args:
        node: The AST node for the function.
        filepath: The path to the file being checked.

    Returns:
        List[str]: List of error messages.
    """
    errors = []
    if not ast.get_docstring(node):
        errors.append(f"Function '{node.name}' in {filepath} missing docstring")
    return errors

def check_class_docstrings(node: ast.ClassDef, filepath: Path) -> List[str]:
    """
    Check if a class has a docstring.

    Args:
        node: The AST node for the class.
        filepath: The path to the file being checked.

    Returns:
        List[str]: List of error messages.
    """
    errors = []
    if not ast.get_docstring(node):
        errors.append(f"Class '{node.name}' in {filepath} missing docstring")

    # Check methods within the class
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(child):
                errors.append(f"Method '{child.name}' in {filepath} missing docstring")
    return errors

def validate_file(filepath: Path) -> List[str]:
    """
    Validate a single Python file for docstrings.

    Args:
        filepath: Path to the Python file.

    Returns:
        List[str]: List of validation error messages.
    """
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=str(filepath))

        # Check module docstring
        module_error = check_module_docstring(tree, filepath)
        if module_error:
            errors.append(module_error)

        # Check functions and classes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                errors.extend(check_function_docstrings(node, filepath))
            elif isinstance(node, ast.ClassDef):
                errors.extend(check_class_docstrings(node, filepath))

    except SyntaxError as e:
        errors.append(f"Syntax error in {filepath}: {e}")
    except Exception as e:
        errors.append(f"Error processing {filepath}: {e}")

    return errors

def run_docstring_check() -> Tuple[int, int]:
    """
    Run docstring validation across all Python files in the code/ directory.

    Returns:
        Tuple[int, int]: (total_files_checked, files_with_errors)
    """
    project_root = get_project_root()
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 0, 0

    python_files = list(code_dir.rglob("*.py"))
    if not python_files:
        logger.warning("No Python files found in code/ directory")
        return 0, 0

    total_errors = 0
    files_with_errors = 0

    logger.info(f"Scanning {len(python_files)} Python files in {code_dir}...")

    for filepath in python_files:
        errors = validate_file(filepath)
        if errors:
            files_with_errors += 1
            total_errors += len(errors)
            logger.error(f"Found {len(errors)} docstring issues in {filepath.relative_to(project_root)}")
            for err in errors:
                logger.error(f"  - {err}")
        else:
            logger.info(f"OK: {filepath.relative_to(project_root)}")

    logger.info(f"Validation complete: {len(python_files)} files checked, {files_with_errors} with errors, {total_errors} total issues")
    return len(python_files), files_with_errors

def main():
    """
    Main entry point for the docstring validation script.

    Runs the validation check and exits with status code 1 if any errors are found,
    otherwise exits with 0.
    """
    total_files, errors_count = run_docstring_check()

    if errors_count > 0:
        logger.error(f"Docstring validation FAILED: {errors_count} files have missing docstrings")
        sys.exit(1)
    else:
        logger.info("Docstring validation PASSED: All files have proper docstrings")
        sys.exit(0)

if __name__ == "__main__":
    main()
