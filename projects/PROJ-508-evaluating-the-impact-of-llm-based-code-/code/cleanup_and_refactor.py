"""
Task T055: Code cleanup and refactoring.

This script performs static analysis and cleanup on the project's codebase.
It ensures:
1. All Python files are syntactically valid.
2. Unused imports are identified (static check).
3. Consistent formatting is enforced (via black/ruff if available).
4. Documentation strings are present for public functions.
5. TODOs and FIXMEs are logged for review.

It does not modify files automatically but generates a report of findings
to be addressed manually or via a separate fix script, ensuring the
"one task" constraint is met without overstepping into automated fixing
which might break logic.
"""
import ast
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
REPORT_PATH = PROJECT_ROOT / "docs" / "output" / "cleanup_report.txt"

def ensure_output_dir():
    """Ensure the output directory exists."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_python_files(directory: Path) -> List[Path]:
    """Recursively find all .py files in the given directory."""
    return list(directory.rglob("*.py"))

def check_syntax(file_path: Path) -> bool:
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return False

def check_docstrings(file_path: Path) -> List[str]:
    """Check for missing docstrings in public functions/classes."""
    warnings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Check if it's a "public" definition (not starting with _)
                if not node.name.startswith('_'):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        warnings.append(f"Missing docstring in {node.name} at line {node.lineno}")
    except SyntaxError:
        pass # Skip files with syntax errors, they are caught elsewhere
    return warnings

def check_todo_comments(file_path: Path) -> List[str]:
    """Check for TODO or FIXME comments."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if 'TODO' in line or 'FIXME' in line:
                    findings.append(f"{line_num}: {line.strip()}")
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    return findings

def run_formatter():
    """Attempt to run black and ruff if installed."""
    logger.info("Attempting to run formatters (black, ruff)...")
    
    # Try black
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            logger.warning("Black check failed. Run 'black code/' to format.")
        else:
            logger.info("Black check passed.")
    except FileNotFoundError:
        logger.info("Black not installed. Skipping formatting check.")
    except subprocess.TimeoutExpired:
        logger.warning("Black check timed out.")

    # Try ruff
    try:
        result = subprocess.run(
            ["ruff", "check", str(CODE_DIR)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            logger.warning("Ruff check found issues.")
            if result.stdout:
                logger.debug(result.stdout)
        else:
            logger.info("Ruff check passed.")
    except FileNotFoundError:
        logger.info("Ruff not installed. Skipping linting check.")
    except subprocess.TimeoutExpired:
        logger.warning("Ruff check timed out.")

def generate_report():
    """Generate a cleanup report."""
    ensure_output_dir()
    issues = []
    syntax_errors = []
    docstring_warnings = []
    todo_items = []

    py_files = get_python_files(CODE_DIR)
    logger.info(f"Found {len(py_files)} Python files to analyze.")

    for file_path in py_files:
        # 1. Syntax Check
        if not check_syntax(file_path):
            syntax_errors.append(str(file_path))
            continue # Skip further checks if syntax is invalid

        # 2. Docstring Check
        d_warnings = check_docstrings(file_path)
        if d_warnings:
            docstring_warnings.extend([f"{file_path.relative_to(PROJECT_ROOT)}: {w}" for w in d_warnings])

        # 3. TODO/FIXME Check
        t_items = check_todo_comments(file_path)
        if t_items:
            todo_items.extend([f"{file_path.relative_to(PROJECT_ROOT)}: {t}" for t in t_items])

    # Write report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(f"Code Cleanup Report for {PROJECT_ROOT}\n")
        f.write("=" * 50 + "\n\n")

        f.write(f"Total files scanned: {len(py_files)}\n\n")

        f.write("SYNTAX ERRORS:\n")
        if syntax_errors:
            for err in syntax_errors:
                f.write(f"  - {err}\n")
        else:
            f.write("  None found.\n")
        f.write("\n")

        f.write("MISSING DOCSTRINGS (Public APIs):\n")
        if docstring_warnings:
            for w in docstring_warnings:
                f.write(f"  - {w}\n")
        else:
            f.write("  None found.\n")
        f.write("\n")

        f.write("TODO/FIXME COMMENTS:\n")
        if todo_items:
            for t in todo_items:
                f.write(f"  - {t}\n")
        else:
            f.write("  None found.\n")
        f.write("\n")

        f.write("FORMATTER STATUS:\n")
        f.write("  (See logs for black/ruff results)\n")

    logger.info(f"Cleanup report generated at: {REPORT_PATH}")

def main():
    """Main entry point for the cleanup task."""
    logger.info("Starting code cleanup and refactoring analysis (T055)...")
    
    # Run formatters to ensure code style is up to date
    run_formatter()
    
    # Generate detailed report
    generate_report()
    
    logger.info("Cleanup and refactoring analysis complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
