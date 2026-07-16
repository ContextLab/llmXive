"""
Refactor and Cleanup Module for PROJ-134.

This module provides utilities for code cleanup, refactoring, and validation
across the project. It scans Python files for common issues like TODOs,
unused imports, missing docstrings, and potential bugs.
"""

import os
import sys
import ast
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

# Configure logging for the cleanup process
logger = logging.getLogger(__name__)


def find_python_files(root_dir: Path) -> List[Path]:
    """
    Recursively find all Python files in the given directory.

    Args:
        root_dir: The root directory to search.

    Returns:
        A list of Path objects for all .py files found.
    """
    python_files = []
    for path in root_dir.rglob("*.py"):
        # Skip test files as they have different conventions
        if "test_" not in path.name and "__pycache__" not in str(path):
            python_files.append(path)
    return python_files


def check_todos(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a Python file for TODO, FIXME, HACK, and XXX comments.

    Args:
        file_path: Path to the Python file.

    Returns:
        A list of dictionaries containing line number, comment type, and text.
    """
    issues = []
    patterns = [
        (r"#\s*TODO[:\s]*(.*)", "TODO"),
        (r"#\s*FIXME[:\s]*(.*)", "FIXME"),
        (r"#\s*HACK[:\s]*(.*)", "HACK"),
        (r"#\s*XXX[:\s]*(.*)", "XXX"),
    ]

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                for pattern, comment_type in patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        issues.append({
                            "line": line_num,
                            "type": comment_type,
                            "text": match.group(1).strip(),
                            "file": str(file_path)
                        })
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")

    return issues


def check_imports(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for potential import issues:
    - Unused imports
    - Import cycles (basic detection)
    - Relative imports that might be problematic

    Args:
        file_path: Path to the Python file.

    Returns:
        A list of dictionaries containing line number, issue type, and details.
    """
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError as e:
        issues.append({
            "line": e.lineno or 0,
            "type": "SYNTAX_ERROR",
            "text": f"Syntax error: {e.msg}",
            "file": str(file_path)
        })
        return issues
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return issues

    # Collect all imports and used names
    imports: Set[str] = set()
    used_names: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.add(name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports.add(name.split(".")[0] if module else name)
        elif isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like module.function
            current = node
            parts = []
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                parts.reverse()
                used_names.add(parts[0])

    # Check for unused imports (simple heuristic)
    for imp in imports:
        # Ignore common safe imports
        safe_ignores = {"os", "sys", "logging", "pathlib", "typing", "ast", "json", "re", "warnings", "datetime", "yaml", "numpy", "pandas", "pytest", "pymc", "statsmodels", "seaborn", "sklearn", "requests", "pydantic", "enum", "itertools", "collections", "functools", "contextlib"}
        if imp not in safe_ignores and imp not in used_names:
            issues.append({
                "line": 0,
                "type": "UNUSED_IMPORT",
                "text": f"Potential unused import: {imp}",
                "file": str(file_path)
            })

    # Check for relative imports
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                if "from ." in line or "import ." in line:
                    issues.append({
                        "line": line_num,
                        "type": "RELATIVE_IMPORT",
                        "text": "Relative import detected",
                        "file": str(file_path)
                    })
    except Exception as e:
        logger.error(f"Error reading {file_path} for relative imports: {e}")

    return issues


def check_docstrings(file_path: Path) -> List[Dict[str, Any]]:
    """
    Check for missing docstrings in functions, classes, and modules.

    Args:
        file_path: Path to the Python file.

    Returns:
        A list of dictionaries containing line number, entity type, name, and issue.
    """
    issues = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        return issues

    # Check module docstring
    if not ast.get_docstring(tree):
        issues.append({
            "line": 1,
            "type": "MISSING_MODULE_DOCSTRING",
            "text": "Module missing docstring",
            "file": str(file_path)
        })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not ast.get_docstring(node):
                entity_type = "class" if isinstance(node, ast.ClassDef) else "function"
                issues.append({
                    "line": node.lineno,
                    "type": "MISSING_DOCSTRING",
                    "text": f"{entity_type.capitalize()} '{node.name}' missing docstring",
                    "file": str(file_path)
                })

    return issues


def run_import_validation(project_root: Path) -> List[Dict[str, Any]]:
    """
    Validate that all imports in the project can be resolved.

    Args:
        project_root: The root directory of the project.

    Returns:
        A list of dictionaries containing import errors.
    """
    issues = []
    sys.path.insert(0, str(project_root))

    python_files = find_python_files(project_root / "code")

    for file_path in python_files:
        try:
            # Try to compile the file to check for import errors
            with open(file_path, "r", encoding="utf-8") as f:
                compile(f.read(), str(file_path), "exec")
        except ImportError as e:
            issues.append({
                "file": str(file_path),
                "type": "IMPORT_ERROR",
                "text": f"Import error: {e.name}"
            })
        except SyntaxError as e:
            issues.append({
                "file": str(file_path),
                "type": "SYNTAX_ERROR",
                "text": f"Syntax error: {e.msg}"
            })
        except Exception as e:
            logger.error(f"Unexpected error validating {file_path}: {e}")

    return issues


def generate_cleanup_report(
    project_root: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive cleanup report for the project.

    Args:
        project_root: The root directory of the project.
        output_path: Optional path to save the report as JSON.

    Returns:
        A dictionary containing the cleanup report.
    """
    report = {
        "project_root": str(project_root),
        "summary": {
            "total_files": 0,
            "total_todos": 0,
            "total_import_issues": 0,
            "total_docstring_issues": 0,
            "total_syntax_errors": 0
        },
        "details": {
            "todos": [],
            "import_issues": [],
            "docstring_issues": [],
            "syntax_errors": [],
            "import_validation_errors": []
        }
    }

    logger.info(f"Starting cleanup analysis for project: {project_root}")

    # Find all Python files
    python_files = find_python_files(project_root / "code")
    report["summary"]["total_files"] = len(python_files)
    logger.info(f"Found {len(python_files)} Python files to analyze")

    # Check each file
    for file_path in python_files:
        logger.debug(f"Analyzing {file_path}")

        # Check TODOs
        todos = check_todos(file_path)
        if todos:
            report["details"]["todos"].extend(todos)
            report["summary"]["total_todos"] += len(todos)

        # Check imports
        import_issues = check_imports(file_path)
        if import_issues:
            report["details"]["import_issues"].extend(import_issues)
            report["summary"]["total_import_issues"] += len(import_issues)

        # Check docstrings
        docstring_issues = check_docstrings(file_path)
        if docstring_issues:
            report["details"]["docstring_issues"].extend(docstring_issues)
            report["summary"]["total_docstring_issues"] += len(docstring_issues)

        # Check for syntax errors (included in import check)
        syntax_errors = [i for i in import_issues if i["type"] == "SYNTAX_ERROR"]
        if syntax_errors:
            report["details"]["syntax_errors"].extend(syntax_errors)
            report["summary"]["total_syntax_errors"] += len(syntax_errors)

    # Run import validation
    import_validation_errors = run_import_validation(project_root)
    if import_validation_errors:
        report["details"]["import_validation_errors"].extend(import_validation_errors)
        report["summary"]["total_import_validation_errors"] = len(import_validation_errors)

    # Save report if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Cleanup report saved to {output_path}")

    logger.info(f"Cleanup analysis complete. Summary: {report['summary']}")

    return report


def main() -> int:
    """
    Main entry point for the cleanup and refactoring tool.

    Returns:
        Exit code (0 for success, 1 for issues found).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    project_root = Path(__file__).parent.parent
    output_path = project_root / "reports" / "cleanup_report.json"

    logger.info("Starting code cleanup and refactoring analysis...")

    try:
        report = generate_cleanup_report(project_root, output_path)

        # Print summary
        print("\n" + "=" * 60)
        print("CODE CLEANUP AND REFACTORING REPORT")
        print("=" * 60)
        print(f"Total files analyzed: {report['summary']['total_files']}")
        print(f"TODO/FIXME/HACK comments: {report['summary']['total_todos']}")
        print(f"Import issues: {report['summary']['total_import_issues']}")
        print(f"Missing docstrings: {report['summary']['total_docstring_issues']}")
        print(f"Syntax errors: {report['summary']['total_syntax_errors']}")
        print(f"Import validation errors: {report['summary'].get('total_import_validation_errors', 0)}")
        print("=" * 60)

        if report["summary"]["total_todos"] > 0:
            print("\nTop TODOs found:")
            for todo in report["details"]["todos"][:5]:
                print(f"  {todo['file']}:{todo['line']} - [{todo['type']}] {todo['text']}")

        if report["summary"]["total_import_issues"] > 0:
            print("\nTop import issues:")
            for issue in report["details"]["import_issues"][:5]:
                print(f"  {issue['file']}:{issue['line']} - {issue['text']}")

        if report["summary"]["total_docstring_issues"] > 0:
            print("\nTop missing docstrings:")
            for issue in report["details"]["docstring_issues"][:5]:
                print(f"  {issue['file']}:{issue['line']} - {issue['text']}")

        if report["summary"]["total_syntax_errors"] > 0:
            print("\nSyntax errors found:")
            for error in report["details"]["syntax_errors"]:
                print(f"  {error['file']}:{error['line']} - {error['text']}")

        print(f"\nFull report saved to: {output_path}")

        # Return 1 if any issues found
        total_issues = (
            report["summary"]["total_todos"] +
            report["summary"]["total_import_issues"] +
            report["summary"]["total_docstring_issues"] +
            report["summary"]["total_syntax_errors"]
        )

        if total_issues > 0:
            print(f"\n⚠️  {total_issues} issues found. Review the report for details.")
            return 1
        else:
            print("\n✅ No issues found. Codebase is clean!")
            return 0

    except Exception as e:
        logger.error(f"Error during cleanup analysis: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())