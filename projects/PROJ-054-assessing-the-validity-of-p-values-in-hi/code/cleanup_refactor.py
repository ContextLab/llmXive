"""
Code cleanup and refactoring utility for the p-value validity project.

This module provides tools to analyze Python files for code quality issues,
refactor them according to best practices, and validate API consistency.
"""
import ast
import os
import re
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Custom exception for cleanup operations
class CodeCleanupError(Exception):
    """Exception raised when code cleanup or refactoring fails."""
    pass

def setup_logging() -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("cleanup_refactor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def extract_imports_from_file(file_path: Path) -> Dict[str, List[str]]:
    """
    Extract all imports from a Python file.

    Args:
        file_path: Path to the Python file.

    Returns:
        Dictionary with keys:
            - 'standard': List of standard library imports
            - 'third_party': List of third-party imports
            - 'local': List of local imports (relative or project-specific)
    """
    logger = logging.getLogger("cleanup_refactor")
    standard_libs = {
        'abc', 'argparse', 'ast', 'asyncio', 'base64', 'bisect', 'builtins',
        'calendar', 'collections', 'concurrent', 'contextlib', 'copy', 'csv',
        'dataclasses', 'datetime', 'decimal', 'difflib', 'dis', 'email',
        'enum', 'errno', 'faulthandler', 'fcntl', 'fileinput', 'fnmatch',
        'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass',
        'gettext', 'glob', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac',
        'html', 'http', 'imaplib', 'importlib', 'inspect', 'io', 'ipaddress',
        'itertools', 'json', 'keyword', 'linecache', 'locale', 'logging',
        'lzma', 'mailbox', 'math', 'mimetypes', 'mmap', 'modulefinder',
        'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator',
        'optparse', 'os', 'ossaudiodev', 'pathlib', 'pdb', 'pickle', 'pickletools',
        'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'posixpath',
        'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr',
        'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib',
        'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select',
        'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd',
        'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3',
        'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
        'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog',
        'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test',
        'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token',
        'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle',
        'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid',
        'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg',
        'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile',
        'zipimport', 'zlib', '_thread', 'typing_extensions'
    }

    imports = {'standard': [], 'third_party': [], 'local': []}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        raise CodeCleanupError(f"Syntax error in {file_path}: {e}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if module_name in standard_libs:
                    imports['standard'].append(alias.name)
                elif module_name.startswith('utils') or module_name in ['numpy', 'scipy', 'matplotlib', 'pandas', 'pytest']:
                    imports['local'].append(alias.name)
                else:
                    imports['third_party'].append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                if node.level > 0:  # Relative import
                    imports['local'].append(f"{'.' * node.level}{node.module}")
                elif module_name in standard_libs:
                    imports['standard'].append(node.module)
                elif module_name.startswith('utils') or module_name in ['numpy', 'scipy', 'matplotlib', 'pandas', 'pytest']:
                    imports['local'].append(node.module)
                else:
                    imports['third_party'].append(node.module)
            else:
                # from X import Y where X is empty (unlikely but handled)
                for alias in node.names:
                    imports['local'].append(alias.name)

    return imports

def analyze_file_for_cleanup(file_path: Path) -> Dict[str, Any]:
    """
    Analyze a Python file for common cleanup opportunities.

    Args:
        file_path: Path to the Python file.

    Returns:
        Dictionary containing analysis results:
            - 'unused_imports': List of potentially unused imports
            - 'long_lines': List of lines exceeding 100 characters
            - 'duplicate_imports': List of duplicate import statements
            - 'missing_docstrings': List of functions/classes missing docstrings
            - 'complex_functions': List of functions with high cyclomatic complexity
    """
    logger = logging.getLogger("cleanup_refactor")
    analysis = {
        'unused_imports': [],
        'long_lines': [],
        'duplicate_imports': [],
        'missing_docstrings': [],
        'complex_functions': [],
        'total_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'blank_lines': 0
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            source = ''.join(lines)
    except Exception as e:
        raise CodeCleanupError(f"Failed to read {file_path}: {e}")

    analysis['total_lines'] = len(lines)

    # Count line types
    in_multiline_string = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            analysis['blank_lines'] += 1
        elif stripped.startswith('"""') or stripped.startswith("'''"):
            in_multiline_string = not in_multiline_string
            if not in_multiline_string:
                analysis['code_lines'] += 1
            else:
                analysis['comment_lines'] += 1
        elif in_multiline_string:
            analysis['comment_lines'] += 1
        elif stripped.startswith('#'):
            analysis['comment_lines'] += 1
        else:
            analysis['code_lines'] += 1

        # Check for long lines
        if len(line.rstrip()) > 100:
            analysis['long_lines'].append({
                'line_num': len(analysis['long_lines']) + 1,
                'length': len(line.rstrip()),
                'content': line.rstrip()[:50] + '...'
            })

    # Parse AST for deeper analysis
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        raise CodeCleanupError(f"Syntax error in {file_path}: {e}")

    # Extract all names defined and used
    defined_names = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            defined_names.add(node.name)
            if not ast.get_docstring(node):
                analysis['missing_docstrings'].append({
                    'type': 'function',
                    'name': node.name,
                    'line': node.lineno
                })

            # Simple complexity check (count branches)
            complexity = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                      ast.With, ast.Assert, ast.comprehension)):
                    complexity += 1
            if complexity > 10:
                analysis['complex_functions'].append({
                    'name': node.name,
                    'complexity': complexity,
                    'line': node.lineno
                })

        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
            if not ast.get_docstring(node):
                analysis['missing_docstrings'].append({
                    'type': 'class',
                    'name': node.name,
                    'line': node.lineno
                })

        elif isinstance(node, ast.Name):
            used_names.add(node.id)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[0]
                defined_names.add(name)

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                defined_names.add(name)

    # Check for unused imports (simplified check)
    imports = extract_imports_from_file(file_path)
    for imp in imports['standard'] + imports['third_party'] + imports['local']:
        name = imp.split('.')[0].split('.')[-1]
        if name.startswith('_'):
            continue  # Ignore private imports
        if name not in used_names:
            analysis['unused_imports'].append({
                'name': imp,
                'line': 0  # Would need more precise tracking
            })

    # Check for duplicate imports
    all_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                all_imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                all_imports.append(node.module)

    seen = set()
    for imp in all_imports:
        if imp in seen:
            analysis['duplicate_imports'].append(imp)
        seen.add(imp)

    return analysis

def refactor_file(file_path: Path, analysis: Dict[str, Any]) -> bool:
    """
    Apply refactoring suggestions to a file.

    Args:
        file_path: Path to the Python file.
        analysis: Analysis results from analyze_file_for_cleanup.

    Returns:
        True if refactoring was successful, False otherwise.
    """
    logger = logging.getLogger("cleanup_refactor")

    if not analysis['unused_imports'] and not analysis['long_lines']:
        logger.info(f"No refactoring needed for {file_path}")
        return True

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return False

    # Remove unused imports (simplified)
    unused_names = {item['name'] for item in analysis['unused_imports']}
    new_lines = []
    for i, line in enumerate(lines):
        skip_line = False
        for unused in unused_names:
            if f"import {unused}" in line or f"from {unused}" in line:
                skip_line = True
                logger.info(f"Removing unused import: {unused} at line {i+1}")
                break
        if not skip_line:
            new_lines.append(line)

    # Write back if changes were made
    if len(new_lines) != len(lines):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logger.info(f"Refactored {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")
            return False

    return True

def validate_apis(project_root: Path) -> Dict[str, List[str]]:
    """
    Validate that all public APIs in the project are consistent.

    Args:
        project_root: Root directory of the project.

    Returns:
        Dictionary with keys:
            - 'missing': List of missing API definitions
            - 'inconsistent': List of inconsistent API definitions
            - 'valid': List of valid API definitions
    """
    logger = logging.getLogger("cleanup_refactor")
    results = {'missing': [], 'inconsistent': [], 'valid': []}

    # Define expected public APIs based on project structure
    expected_apis = {
        'code/utils/exceptions.py': ['HighDimensionalInstabilityError', 'SimulationError',
                                     'DataGenerationError', 'HypothesisTestError', 'AnalysisError'],
        'code/utils/regularization.py': ['is_condition_number_acceptable', 'regularize_covariance'],
        'code/utils/simulation.py': ['SimulationConfig', 'SyntheticDataset', 'MemoryMonitor',
                                     'SimulationOrchestrator', 'main'],
        'code/generate_data.py': ['generate_correlated_data', 'generate_distribution_violations',
                                  'write_dataset_metadata', 'main'],
        'code/run_tests.py': ['run_hypothesis_tests', 'run_hypothesis_tests_batch', 'main'],
        'code/analyze_pvalues.py': ['generate_permutation_reference', 'calculate_ks_statistic', 'main'],
        'code/bootstrap_ci.py': ['calculate_bootstrap_ci', 'load_trajectory_data',
                                 'run_bootstrap_analysis', 'main'],
        'code/cleanup_refactor.py': ['CodeCleanupError', 'setup_logging', 'extract_imports_from_file',
                                     'analyze_file_for_cleanup', 'refactor_file', 'validate_apis',
                                     'run_cleanup', 'main'],
        'code/collect_pvalues.py': ['collect_pvalues', 'aggregate_pvalues', 'write_trajectory_snapshot', 'main'],
        'code/plot_qq.py': ['load_pvalue_trajectories', 'aggregate_pvalues', 'generate_qq_plot', 'main'],
        'code/sensitivity_analysis.py': ['load_trajectories_for_rho', 'calculate_ks_statistic_for_rho',
                                         'run_sensitivity_analysis', 'main'],
        'code/store_trajectories.py': ['compute_trajectory_hash', 'write_trajectory_file', 'main'],
        'code/integrate_pipeline.py': ['load_simulation_configs', 'run_integration_pipeline', 'main'],
        'code/docs_generator.py': ['generate_methodology_doc', 'generate_data_generation_doc',
                                   'generate_analysis_doc', 'generate_readme', 'write_documentation_files', 'main'],
        'code/profile_simulation.py': ['get_memory_usage_mb', 'run_profiled_sweep', 'write_profile_report', 'main']
    }

    for rel_path, expected_names in expected_apis.items():
        file_path = project_root / rel_path
        if not file_path.exists():
            results['missing'].append(f"{rel_path} (file missing)")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            results['missing'].append(f"{rel_path} (parse error: {e})")
            continue

        # Extract public names
        public_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'):
                    public_names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        public_names.add(target.id)

        # Check for missing or extra
        missing = set(expected_names) - public_names
        extra = public_names - set(expected_names)

        if missing:
            results['missing'].append(f"{rel_path}: missing {list(missing)}")
        elif extra:
            results['inconsistent'].append(f"{rel_path}: extra {list(extra)}")
        else:
            results['valid'].append(rel_path)

    return results

def run_cleanup(project_root: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run cleanup and refactoring on all Python files in the project.

    Args:
        project_root: Root directory of the project.
        dry_run: If True, only analyze without modifying files.

    Returns:
        Dictionary containing cleanup results.
    """
    logger = logging.getLogger("cleanup_refactor")
    results = {
        'files_analyzed': 0,
        'files_refactored': 0,
        'issues_found': 0,
        'api_validation': {},
        'details': []
    }

    # Find all Python files
    py_files = list(project_root.glob('code/**/*.py'))

    for file_path in py_files:
        results['files_analyzed'] += 1
        logger.info(f"Analyzing {file_path}")

        try:
            analysis = analyze_file_for_cleanup(file_path)
            total_issues = (
                len(analysis['unused_imports']) +
                len(analysis['long_lines']) +
                len(analysis['duplicate_imports']) +
                len(analysis['missing_docstrings']) +
                len(analysis['complex_functions'])
            )

            if total_issues > 0:
                results['issues_found'] += total_issues
                results['details'].append({
                    'file': str(file_path.relative_to(project_root)),
                    'issues': {
                        'unused_imports': len(analysis['unused_imports']),
                        'long_lines': len(analysis['long_lines']),
                        'duplicate_imports': len(analysis['duplicate_imports']),
                        'missing_docstrings': len(analysis['missing_docstrings']),
                        'complex_functions': len(analysis['complex_functions'])
                    }
                })

                if not dry_run:
                    if refactor_file(file_path, analysis):
                        results['files_refactored'] += 1
        except CodeCleanupError as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            results['details'].append({
                'file': str(file_path.relative_to(project_root)),
                'error': str(e)
            })

    # Validate APIs
    logger.info("Validating APIs...")
    results['api_validation'] = validate_apis(project_root)

    return results

def main():
    """Main entry point for the cleanup and refactoring script."""
    logger = setup_logging()
    logger.info("Starting code cleanup and refactoring...")

    project_root = Path(__file__).resolve().parent.parent
    dry_run = '--dry-run' in sys.argv

    results = run_cleanup(project_root, dry_run=dry_run)

    logger.info(f"Analysis complete. Files analyzed: {results['files_analyzed']}")
    logger.info(f"Issues found: {results['issues_found']}")
    logger.info(f"Files refactored: {results['files_refactored']}")

    if results['api_validation']['missing']:
        logger.warning(f"Missing APIs: {results['api_validation']['missing']}")
    if results['api_validation']['inconsistent']:
        logger.warning(f"Inconsistent APIs: {results['api_validation']['inconsistent']}")
    logger.info(f"Valid APIs: {len(results['api_validation']['valid'])}")

    if dry_run:
        logger.info("Dry run mode - no files were modified.")

    return 0 if results['issues_found'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())