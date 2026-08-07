"""
Code cleanup and refactoring utility for the llmXive p-value validity pipeline.

This module provides functions to:
1. Analyze Python files for common code quality issues (unused imports, duplicate code, long functions).
2. Refactor files to improve readability and maintainability.
3. Validate that public APIs match the expected interface.
4. Run a full cleanup sweep across the project's code directory.
"""
import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CodeCleanupError(Exception):
    """Custom exception for code cleanup operations."""
    pass


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the cleanup process."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(level)


def extract_imports_from_file(file_path: Path) -> Tuple[Set[str], Set[str]]:
    """
    Extract all imports from a Python file.

    Returns:
        Tuple of (standard_library_imports, third_party_imports)
    """
    if not file_path.exists():
        raise CodeCleanupError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CodeCleanupError(f"Syntax error in {file_path}: {e}")

    standard_lib = set()
    third_party = set()

    # Known standard library modules (comprehensive list)
    stdlib_modules = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio',
        'asyncore', 'atexit', 'audioop', 'base64', 'bdb', 'binascii',
        'binhex', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb',
        'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
        'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib',
        'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
        'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
        'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
        'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput',
        'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
        'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib',
        'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp',
        'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json',
        'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma',
        'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap',
        'modulefinder', 'multiprocessing', 'netrc', 'nis', 'nntplib',
        'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'pathlib',
        'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
        'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile',
        'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue',
        'quopri', 'random', 're', 'readline', 'reprlib', 'resource',
        'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors',
        'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
        'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl',
        'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess',
        'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
        'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
        'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize',
        'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo',
        'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu',
        'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
        'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc',
        'zipapp', 'zipfile', 'zipimport', 'zlib', '_thread'
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if module_name in stdlib_modules:
                    standard_lib.add(alias.name)
                else:
                    third_party.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                if module_name in stdlib_modules:
                    standard_lib.add(node.module)
                else:
                    third_party.add(node.module)

    return standard_lib, third_party


def analyze_file_for_cleanup(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a Python file for common code quality issues.

    Returns a dictionary with:
    - unused_imports: list of unused imports
    - long_functions: list of functions with > 50 lines
    - duplicate_code: list of potentially duplicated code blocks
    - complexity_score: estimated cyclomatic complexity
    """
    if not file_path.exists():
        raise CodeCleanupError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
        lines = source.splitlines()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {
            'error': f"Syntax error: {e}",
            'unused_imports': [],
            'long_functions': [],
            'duplicate_code': [],
            'complexity_score': 0
        }

    # Extract all names defined and used in the file
    defined_names = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[-1]
                defined_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                defined_names.add(name)
        elif isinstance(node, ast.Name):
            used_names.add(node.id)

    # Find unused imports
    unused_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[-1]
                if name not in used_names:
                    unused_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                if name not in used_names:
                    unused_imports.append(f"{node.module}.{name}" if node.module else name)

    # Find long functions
    long_functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Calculate function length
            start_line = node.lineno
            end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
            length = end_line - start_line + 1
            if length > 50:
                long_functions.append({
                    'name': node.name,
                    'lines': length,
                    'start': start_line,
                    'end': end_line
                })

    # Calculate cyclomatic complexity
    complexity_score = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                             ast.With, ast.Assert, ast.comprehension)):
            complexity_score += 1
        elif isinstance(node, ast.BoolOp):
            complexity_score += len(node.values) - 1

    # Simple duplicate code detection (exact line matches)
    line_counts = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            if stripped in line_counts:
                line_counts[stripped].append(i)
            else:
                line_counts[stripped] = [i]

    duplicate_code = []
    for line_content, line_numbers in line_counts.items():
        if len(line_numbers) > 3 and len(line_content) > 20:
            duplicate_code.append({
                'content': line_content[:50] + '...',
                'occurrences': len(line_numbers),
                'lines': line_numbers
            })

    return {
        'unused_imports': unused_imports,
        'long_functions': long_functions,
        'duplicate_code': duplicate_code,
        'complexity_score': complexity_score,
        'total_lines': len(lines),
        'code_lines': len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    }


def refactor_file(file_path: Path, analysis: Dict[str, Any]) -> bool:
    """
    Refactor a file based on analysis results.

    Currently implements:
    - Removing unused imports
    - Splitting long functions (placeholder for future implementation)

    Returns True if changes were made, False otherwise.
    """
    if 'error' in analysis:
        logger.warning(f"Skipping refactor due to error: {analysis['error']}")
        return False

    if not analysis['unused_imports']:
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Remove unused imports
    unused_set = set(analysis['unused_imports'])
    modified_lines = []
    changed = False

    for line in lines:
        # Check if this line is an import that should be removed
        is_unused_import = False
        stripped = line.strip()

        if stripped.startswith('import '):
            module = stripped[7:].split(',')[0].strip()
            if module in unused_set:
                is_unused_import = True
        elif stripped.startswith('from '):
            parts = stripped.split()
            if len(parts) >= 4:
                module = parts[1]
                imports = parts[3].split(',')
                for imp in imports:
                    imp_name = imp.strip()
                    if imp_name in unused_set:
                        is_unused_import = True
                        break

        if is_unused_import:
            logger.info(f"Removing unused import: {stripped}")
            changed = True
        else:
            modified_lines.append(line)

    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)
        logger.info(f"Refactored {file_path}: removed {len(unused_set)} unused imports")

    return changed


def validate_apis(file_path: Path, expected_apis: Set[str]) -> List[str]:
    """
    Validate that a file exports the expected public APIs.

    Returns a list of missing APIs.
    """
    if not file_path.exists():
        raise CodeCleanupError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CodeCleanupError(f"Syntax error in {file_path}: {e}")

    # Find all public names (not starting with _)
    public_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith('_'):
                public_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith('_'):
                    public_names.add(target.id)

    missing_apis = []
    for api in expected_apis:
        if api not in public_names:
            missing_apis.append(api)

    return missing_apis


def run_cleanup(project_root: Path, code_dir: str = "code") -> Dict[str, Any]:
    """
    Run cleanup and refactoring across all Python files in the project.

    Returns a summary of actions taken.
    """
    code_path = project_root / code_dir
    if not code_path.exists():
        raise CodeCleanupError(f"Code directory not found: {code_path}")

    results = {
        'files_analyzed': 0,
        'files_refactored': 0,
        'issues_found': [],
        'apis_validated': 0,
        'missing_apis': []
    }

    # Define expected APIs for known modules
    expected_apis_map = {
        'analyze_pvalues.py': {'generate_permutation_reference', 'calculate_ks_statistic', 'main'},
        'bootstrap_ci.py': {'calculate_bootstrap_ci', 'load_trajectory_data', 'run_bootstrap_analysis', 'main'},
        'cleanup_refactor.py': {'CodeCleanupError', 'setup_logging', 'extract_imports_from_file',
                                'analyze_file_for_cleanup', 'refactor_file', 'run_cleanup',
                                'validate_apis', 'main'},
        'collect_pvalues.py': {'collect_pvalues', 'aggregate_pvalues', 'write_trajectory_snapshot', 'main'},
        'generate_data.py': {'generate_correlated_data', 'generate_distribution_violations',
                             'write_dataset_metadata', 'main'},
        'integrate_pipeline.py': {'load_simulation_configs', 'run_integration_pipeline', 'main'},
        'plot_qq.py': {'load_pvalue_trajectories', 'aggregate_pvalues', 'generate_qq_plot', 'main'},
        'profile_simulation.py': {'get_memory_usage_mb', 'run_profiled_sweep', 'write_profile_report', 'main'},
        'run_tests.py': {'run_hypothesis_tests', 'run_hypothesis_tests_batch', 'main'},
        'sensitivity_analysis.py': {'load_trajectories_for_rho', 'calculate_ks_statistic_for_rho',
                                    'run_sensitivity_analysis', 'main'},
        'store_trajectories.py': {'compute_trajectory_hash', 'write_trajectory_file', 'main'},
    }

    py_files = list(code_path.rglob("*.py"))

    for py_file in py_files:
        logger.info(f"Analyzing {py_file}")
        results['files_analyzed'] += 1

        try:
            analysis = analyze_file_for_cleanup(py_file)

            # Log issues
            if analysis['unused_imports']:
                results['issues_found'].append({
                    'file': str(py_file.relative_to(project_root)),
                    'issue': 'unused_imports',
                    'details': analysis['unused_imports']
                })

            if analysis['long_functions']:
                results['issues_found'].append({
                    'file': str(py_file.relative_to(project_root)),
                    'issue': 'long_functions',
                    'details': [f"{f['name']} ({f['lines']} lines)" for f in analysis['long_functions']]
                })

            if analysis['complexity_score'] > 15:
                results['issues_found'].append({
                    'file': str(py_file.relative_to(project_root)),
                    'issue': 'high_complexity',
                    'details': f"Cyclomatic complexity: {analysis['complexity_score']}"
                })

            # Attempt refactor
            if analyze_file_for_cleanup(py_file)['unused_imports']:
                if refactor_file(py_file, analysis):
                    results['files_refactored'] += 1

            # Validate APIs
            filename = py_file.name
            if filename in expected_apis_map:
                missing = validate_apis(py_file, expected_apis_map[filename])
                results['apis_validated'] += 1
                if missing:
                    results['missing_apis'].append({
                        'file': str(py_file.relative_to(project_root)),
                        'missing': missing
                    })

        except CodeCleanupError as e:
            logger.error(f"Error processing {py_file}: {e}")
            results['issues_found'].append({
                'file': str(py_file.relative_to(project_root)),
                'issue': 'error',
                'details': str(e)
            })

    return results


def main():
    """Main entry point for the cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(description='Code cleanup and refactoring tool')
    parser.add_argument('--project-root', type=Path, default=Path('.'),
                        help='Project root directory')
    parser.add_argument('--code-dir', type=str, default='code',
                        help='Code directory relative to project root')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')

    args = parser.parse_args()

    setup_logging(args.log_level)

    try:
        results = run_cleanup(args.project_root, args.code_dir)

        logger.info(f"\nCleanup Summary:")
        logger.info(f"  Files analyzed: {results['files_analyzed']}")
        logger.info(f"  Files refactored: {results['files_refactored']}")
        logger.info(f"  Issues found: {len(results['issues_found'])}")
        logger.info(f"  APIs validated: {results['apis_validated']}")

        if results['missing_apis']:
            logger.warning("Missing APIs detected:")
            for missing in results['missing_apis']:
                logger.warning(f"  {missing['file']}: {missing['missing']}")

        if results['issues_found']:
            logger.info("Issues found:")
            for issue in results['issues_found'][:10]:  # Show first 10
                logger.info(f"  {issue['file']}: {issue['issue']}")
            if len(results['issues_found']) > 10:
                logger.info(f"  ... and {len(results['issues_found']) - 10} more")

    except CodeCleanupError as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()