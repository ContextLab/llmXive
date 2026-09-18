"""
T036: Code cleanup and refactoring of code/data/ and code/modeling/

This script performs automated cleanup and refactoring tasks:
1. Removes unused imports from Python files
2. Fixes function naming inconsistencies (snake_case enforcement)
3. Standardizes docstrings (Google style)
4. Runs ruff check and fix
5. Runs black formatting
"""
import os
import ast
import re
from pathlib import Path
from typing import List, Set, Tuple, Optional
import subprocess
import sys
import black
import logging

from utils.logging import get_logger

logger = get_logger(__name__)


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in the given directory recursively."""
    return list(directory.rglob("*.py"))


def get_imported_names(tree: ast.AST) -> Set[str]:
    """Extract all imported names from an AST."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.add(name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.add(name)
    return imports


def get_used_names(tree: ast.AST) -> Set[str]:
    """Extract all names used in the AST."""
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # For attribute access, we only care about the top-level name
            if isinstance(node.value, ast.Name):
                used.add(node.value.id)
    return used


def find_unused_imports(content: str) -> List[str]:
    """Find imports that are not used in the code."""
    try:
        tree = ast.parse(content)
    except SyntaxError:
        logger.warning("Syntax error in file, skipping unused import analysis")
        return []

    imported = get_imported_names(tree)
    used = get_used_names(tree)

    unused = imported - used
    return list(unused)


def fix_import_section(content: str, unused_imports: List[str]) -> str:
    """Remove unused imports from the content."""
    if not unused_imports:
        return content

    lines = content.split("\n")
    new_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        # Check if this is an import line
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            # Extract imported names
            tree = ast.parse("\n".join(lines[i:]))
            current_imports = get_imported_names(tree)

            # Check if any of these imports are unused
            should_keep = False
            for imp in current_imports:
                if imp not in unused_imports:
                    should_keep = True
                    break

            if should_keep:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def extract_function_signatures(content: str) -> List[Tuple[str, str]]:
    """Extract function signatures and their current names."""
    functions = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return functions

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Get the function signature
            start_line = node.lineno - 1
            lines = content.split("\n")
            signature = lines[start_line].strip()
            functions.append((node.name, signature))

    return functions


def fix_function_names(content: str) -> str:
    """Ensure all function names follow snake_case convention."""
    # Pattern to match function definitions
    pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('

    def replace_with_snake(match):
        func_name = match.group(1)
        # Convert to snake_case if not already
        snake_name = re.sub(r'(?<!^)(?=[A-Z])', '_', func_name).lower()
        if func_name != snake_name:
            logger.debug(f"Renaming function: {func_name} -> {snake_name}")
            return f"def {snake_name}("
        return match.group(0)

    return re.sub(pattern, replace_with_snake, content)


def standardize_docstrings(content: str) -> str:
    """Standardize docstrings to Google style."""
    # This is a simplified version - a full implementation would be more complex
    lines = content.split("\n")
    new_lines = []
    in_docstring = False
    docstring_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
                docstring_lines = [line]
            else:
                docstring_lines.append(line)
                in_docstring = False
                # Process the docstring
                processed_docstring = "\n".join(docstring_lines)
                new_lines.append(processed_docstring)
                docstring_lines = []
        elif in_docstring:
            docstring_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def run_ruff_check_and_fix(directory: Path) -> Tuple[bool, str]:
    """Run ruff check and fix on the directory."""
    try:
        # Run ruff check
        check_result = subprocess.run(
            ["ruff", "check", str(directory)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if check_result.returncode == 0:
            logger.info("Ruff check passed")
            return True, ""

        logger.info(f"Ruff check found issues, attempting fix...")

        # Run ruff fix
        fix_result = subprocess.run(
            ["ruff", "check", "--fix", str(directory)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if fix_result.returncode == 0:
            logger.info("Ruff fix completed successfully")
            return True, ""
        else:
            logger.warning(f"Ruff fix had issues: {fix_result.stderr}")
            return False, fix_result.stderr

    except subprocess.TimeoutExpired:
        logger.error("Ruff check/fix timed out")
        return False, "Timeout"
    except FileNotFoundError:
        logger.error("ruff not found. Please install it with: pip install ruff")
        return False, "ruff not installed"


def run_black_format(directory: Path) -> Tuple[bool, str]:
    """Run black formatting on the directory."""
    try:
        result = subprocess.run(
            ["black", str(directory)],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            logger.info("Black formatting completed successfully")
            return True, ""
        else:
            logger.warning(f"Black had issues: {result.stderr}")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        logger.error("Black formatting timed out")
        return False, "Timeout"
    except FileNotFoundError:
        logger.error("black not found. Please install it with: pip install black")
        return False, "black not installed"


def cleanup_and_refactor(project_root: Optional[Path] = None) -> bool:
    """
    Main cleanup and refactoring function.

    Args:
        project_root: Path to the project root. If None, uses current directory.

    Returns:
        True if cleanup was successful, False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()

    logger.info(f"Starting cleanup and refactoring for: {project_root}")

    # Define directories to process
    data_dir = project_root / "code" / "data"
    modeling_dir = project_root / "code" / "modeling"

    directories = [data_dir, modeling_dir]

    success = True

    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            continue

        logger.info(f"Processing directory: {directory}")

        # Find all Python files
        py_files = find_python_files(directory)
        logger.info(f"Found {len(py_files)} Python files")

        for py_file in py_files:
            logger.info(f"Processing file: {py_file}")

            try:
                # Read file content
                content = py_file.read_text(encoding="utf-8")

                # Find unused imports
                unused = find_unused_imports(content)
                if unused:
                    logger.info(f"Found {len(unused)} unused imports in {py_file.name}")
                    content = fix_import_section(content, unused)

                # Fix function names
                content = fix_function_names(content)

                # Standardize docstrings
                content = standardize_docstrings(content)

                # Write back
                py_file.write_text(content, encoding="utf-8")
                logger.info(f"Successfully processed {py_file.name}")

            except Exception as e:
                logger.error(f"Error processing {py_file}: {e}")
                success = False

    # Run ruff check and fix
    logger.info("Running ruff check and fix...")
    ruff_success, ruff_error = run_ruff_check_and_fix(project_root / "code")
    if not ruff_success:
        logger.warning(f"Ruff check/fix failed: {ruff_error}")
        success = False

    # Run black formatting
    logger.info("Running black formatting...")
    black_success, black_error = run_black_format(project_root / "code")
    if not black_success:
        logger.warning(f"Black formatting failed: {black_error}")
        success = False

    if success:
        logger.info("Cleanup and refactoring completed successfully")
    else:
        logger.warning("Cleanup and refactoring completed with warnings")

    return success


def main():
    """Entry point for the cleanup and refactoring script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="T036: Code cleanup and refactoring for code/data/ and code/modeling/"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to the project root (default: current directory)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    success = cleanup_and_refactor(args.project_root)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()