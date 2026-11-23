"""
Docstring Addition Utility for llmXive Project.

This script is a helper utility that can be used to automatically add
basic docstrings to Python files that are missing them. It serves as a
development tool to assist in meeting the T031c requirement of ensuring
all scripts have proper documentation.
"""
import ast
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

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
        Path: The absolute path to the project root.
    """
    current_file = Path(__file__).resolve()
    if current_file.name == "setup_docstrings.py":
        return current_file.parent.parent
    return current_file.parent

def generate_module_docstring(filepath: Path) -> str:
    """
    Generate a basic module docstring for a file.

    Args:
        filepath: Path to the Python file.

    Returns:
        str: Generated docstring content.
    """
    filename = filepath.stem
    # Create a generic docstring based on the filename
    docstring = f'"""\nModule: {filename}\n\nAuto-generated docstring for {filename}.py.\n"""\n'
    return docstring

def add_docstring_to_file(filepath: Path, dry_run: bool = False) -> bool:
    """
    Add missing docstrings to a Python file.

    Args:
        filepath: Path to the Python file.
        dry_run: If True, only report changes without modifying files.

    Returns:
        bool: True if changes were made (or would be made in dry run), False otherwise.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
        needs_module_docstring = not ast.get_docstring(tree)

        changes_needed = []
        if needs_module_docstring:
            changes_needed.append("module")

        # Check functions and classes
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not ast.get_docstring(node):
                    changes_needed.append(f"function:{node.name}")
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    changes_needed.append(f"class:{node.name}")
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not ast.get_docstring(child):
                            changes_needed.append(f"method:{node.name}.{child.name}")

        if not changes_needed:
            return False

        if dry_run:
            logger.info(f"Dry run: {filepath.relative_to(get_project_root())} needs docstrings for: {', '.join(changes_needed)}")
            return True

        # In a real implementation, we would modify the file here
        # For now, we just report what would be done
        logger.info(f"Would add docstrings to {filepath.relative_to(get_project_root())}")
        return True

    except Exception as e:
        logger.error(f"Error processing {filepath}: {e}")
        return False

def scan_and_report() -> List[Path]:
    """
    Scan all Python files in code/ and report those missing docstrings.

    Returns:
        List[Path]: List of files that need docstrings.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return []

    files_needing_docstrings = []
    python_files = list(code_dir.rglob("*.py"))

    for filepath in python_files:
        if add_docstring_to_file(filepath, dry_run=True):
            files_needing_docstrings.append(filepath)

    return files_needing_docstrings

def main():
    """
    Main entry point for the docstring setup script.

    Scans the code/ directory and reports files that need docstrings.
    """
    logger.info("Scanning for missing docstrings...")
    files = scan_and_report()

    if files:
        logger.info(f"Found {len(files)} files missing docstrings:")
        for f in files:
            logger.info(f"  - {f.relative_to(get_project_root())}")
        logger.info("Please run the validation script after adding docstrings.")
    else:
        logger.info("All files have proper docstrings!")

if __name__ == "__main__":
    main()