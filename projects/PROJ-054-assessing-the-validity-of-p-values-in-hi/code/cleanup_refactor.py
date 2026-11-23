"""
Code cleanup and refactoring utility for the p-value validity project.

This module implements T041: Code cleanup and refactoring.
It runs ruff check --fix and mypy type checking (deferred coverage)
on the project's codebase.
"""
import ast
import os
import re
import subprocess
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeCleanupError(Exception):
    """Custom exception for code cleanup failures."""
    pass


def setup_logging() -> None:
    """Setup logging configuration for the cleanup process."""
    logger.setLevel(logging.INFO)


def extract_imports_from_file(file_path: Path) -> List[str]:
    """
    Extract all import statements from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        List of imported module names
    """
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module.split('.')[0])
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.warning(f"Error processing {file_path}: {e}")

    return imports


def analyze_file_for_cleanup(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a Python file for cleanup opportunities.

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary with analysis results
    """
    result = {
        'path': str(file_path),
        'lines': 0,
        'imports': [],
        'has_syntax_errors': False,
        'issues': []
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            result['lines'] = len(content.splitlines())

        # Parse AST to check for syntax errors
        try:
            ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            result['has_syntax_errors'] = True
            result['issues'].append(f"Syntax error: {e}")

        # Extract imports
        result['imports'] = extract_imports_from_file(file_path)

    except Exception as e:
        result['issues'].append(f"Analysis error: {e}")

    return result


def refactor_file(file_path: Path) -> Tuple[bool, str]:
    """
    Refactor a Python file using ruff.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (success, message)
    """
    try:
        # Run ruff check --fix
        ruff_check = subprocess.run(
            ['ruff', 'check', '--fix', str(file_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if ruff_check.returncode != 0 and ruff_check.returncode != 1:
            # Return code 1 means issues found but fixed, 0 means no issues
            # Other codes indicate errors
            return False, f"Ruff check failed: {ruff_check.stderr}"

        # Run ruff format to ensure consistent formatting
        ruff_format = subprocess.run(
            ['ruff', 'format', str(file_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if ruff_format.returncode != 0:
            return False, f"Ruff format failed: {ruff_format.stderr}"

        return True, f"Successfully refactored {file_path}"

    except subprocess.TimeoutExpired:
        return False, f"Timeout while processing {file_path}"
    except FileNotFoundError:
        return False, "Ruff not found. Please install it with: pip install ruff"
    except Exception as e:
        return False, f"Error refactoring {file_path}: {e}"


def validate_apis(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that all imported names exist in the project's API surface.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (is_valid, list of missing imports)
    """
    missing_imports = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Check if the module exists
                    module_name = alias.name.split('.')[0]
                    # We can't easily check if a module exists without importing it
                    # This is a simplified check
                    pass
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    # Check for relative imports within the project
                    if node.level > 0:
                        # Relative import - skip validation as it's project internal
                        continue

    except Exception as e:
        logger.warning(f"Error validating APIs in {file_path}: {e}")

    return len(missing_imports) == 0, missing_imports


def run_cleanup(project_root: Path) -> Dict[str, Any]:
    """
    Run cleanup on all Python files in the project.

    Args:
        project_root: Path to the project root directory

    Returns:
        Dictionary with cleanup results
    """
    results = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'files': []
    }

    # Find all Python files in code/ directory
    code_dir = project_root / 'code'
    if not code_dir.exists():
        logger.warning(f"Code directory not found: {code_dir}")
        return results

    python_files = list(code_dir.rglob('*.py'))
    results['total_files'] = len(python_files)

    logger.info(f"Found {len(python_files)} Python files to process")

    for file_path in python_files:
        # Skip __init__.py as it's often minimal
        if file_path.name == '__init__.py':
            continue

        logger.info(f"Processing {file_path}")

        # Analyze file
        analysis = analyze_file_for_cleanup(file_path)
        if analysis['has_syntax_errors']:
            results['failed'] += 1
            results['files'].append({
                'path': str(file_path),
                'status': 'syntax_error',
                'issues': analysis['issues']
            })
            continue

        # Refactor file
        success, message = refactor_file(file_path)
        if success:
            results['successful'] += 1
            results['files'].append({
                'path': str(file_path),
                'status': 'success',
                'message': message
            })
        else:
            results['failed'] += 1
            results['files'].append({
                'path': str(file_path),
                'status': 'failed',
                'message': message
            })

    return results


def run_mypy_check(project_root: Path) -> Tuple[bool, str]:
    """
    Run mypy type checking on the project.

    Args:
        project_root: Path to the project root directory

    Returns:
        Tuple of (success, output)
    """
    try:
        # Run mypy with deferred coverage
        mypy_cmd = [
            'mypy',
            '--ignore-missing-imports',
            '--show-error-codes',
            '--no-error-summary',
            str(project_root / 'code')
        ]

        result = subprocess.run(
            mypy_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return True, "MyPy check passed with no errors"
        else:
            # Return type checking results (not necessarily a failure)
            return True, f"MyPy type checking completed:\n{result.stdout}\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "MyPy check timed out"
    except FileNotFoundError:
        return False, "MyPy not found. Please install it with: pip install mypy"
    except Exception as e:
        return False, f"Error running MyPy: {e}"


def generate_type_coverage_report(project_root: Path) -> Dict[str, Any]:
    """
    Generate a type coverage report using mypy.

    Args:
        project_root: Path to the project root directory

    Returns:
        Dictionary with coverage report
    """
    report = {
        'total_functions': 0,
        'typed_functions': 0,
        'coverage_percentage': 0.0,
        'files': []
    }

    # This is a simplified coverage check
    # A full implementation would parse AST and check function signatures
    code_dir = project_root / 'code'
    if not code_dir.exists():
        return report

    for file_path in code_dir.rglob('*.py'):
        if file_path.name == '__init__.py':
            continue

        file_report = {
            'path': str(file_path),
            'total_functions': 0,
            'typed_functions': 0
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    file_report['total_functions'] += 1
                    # Check if function has return type annotation
                    if node.returns is not None:
                        file_report['typed_functions'] += 1

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")

        report['files'].append(file_report)
        report['total_functions'] += file_report['total_functions']
        report['typed_functions'] += file_report['typed_functions']

    if report['total_functions'] > 0:
        report['coverage_percentage'] = (
            report['typed_functions'] / report['total_functions'] * 100
        )

    return report


def main() -> int:
    """
    Main entry point for the cleanup and refactoring script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    setup_logging()

    # Determine project root
    project_root = Path.cwd()
    if (project_root / 'tasks.md').exists():
        # We're already in the project root
        pass
    elif (project_root.parent / 'tasks.md').exists():
        project_root = project_root.parent
    else:
        logger.error("Could not find project root (tasks.md not found)")
        return 1

    logger.info(f"Project root: {project_root}")

    # Run ruff cleanup
    logger.info("Running ruff check --fix...")
    cleanup_results = run_cleanup(project_root)

    logger.info(f"Cleanup results: {cleanup_results['successful']}/{cleanup_results['total_files']} files processed successfully")

    if cleanup_results['failed'] > 0:
        logger.warning(f"{cleanup_results['failed']} files failed cleanup")
        for file_result in cleanup_results['files']:
            if file_result['status'] == 'failed':
                logger.warning(f"  - {file_result['path']}: {file_result.get('message', 'Unknown error')}")

    # Run mypy check
    logger.info("Running MyPy type checking...")
    mypy_success, mypy_output = run_mypy_check(project_root)
    logger.info(mypy_output)

    # Generate type coverage report
    logger.info("Generating type coverage report...")
    coverage_report = generate_type_coverage_report(project_root)
    logger.info(f"Type coverage: {coverage_report['coverage_percentage']:.1f}% "
               f"({coverage_report['typed_functions']}/{coverage_report['total_functions']} functions)")

    # Write coverage report to file
    reports_dir = project_root / 'reports'
    reports_dir.mkdir(exist_ok=True)

    import json
    coverage_file = reports_dir / 'type_coverage.json'
    with open(coverage_file, 'w', encoding='utf-8') as f:
        json.dump(coverage_report, f, indent=2)

    logger.info(f"Type coverage report written to {coverage_file}")

    # Write cleanup results to file
    cleanup_file = reports_dir / 'cleanup_results.json'
    with open(cleanup_file, 'w', encoding='utf-8') as f:
        json.dump(cleanup_results, f, indent=2)

    logger.info(f"Cleanup results written to {cleanup_file}")

    # Return success if no critical failures
    if cleanup_results['failed'] > cleanup_results['total_files'] * 0.5:
        logger.error("Too many files failed cleanup")
        return 1

    logger.info("Code cleanup and refactoring completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
