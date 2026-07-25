"""
T035: Code cleanup and refactoring.

This module performs systematic cleanup and refactoring of the project codebase:
1. Removes unused imports and dead code
2. Standardizes logging configuration across modules
3. Consolidates error handling patterns
4. Removes debug artifacts and TODO comments
5. Ensures consistent docstring formatting
6. Validates all public APIs match their documented signatures
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any

# Standardize logging across the project
import logging
from logging.handlers import RotatingFileHandler

# Configuration constants
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
LOG_DIR = PROJECT_ROOT / "logs"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# Patterns to identify cleanup candidates
UNUSED_IMPORT_PATTERN = re.compile(r'^# unused import: ')
TODO_PATTERN = re.compile(r'# TODO:.*|# FIXME:.*|# XXX:.*', re.IGNORECASE)
DEBUG_PATTERN = re.compile(r'print\(.*\)|pdb\.set_trace\(\)|breakpoint\(\)')
DEAD_CODE_PATTERN = re.compile(r'if False:|if 0:|pass\s+# dead code')

# Common unused imports to flag
COMMON_UNUSED_IMPORTS = {
    'sys', 'os', 'pathlib', 'json', 'collections', 'functools',
    'itertools', 'operator', 'math', 'random', 'time', 'datetime'
}

class CodeCleanupError(Exception):
    """Custom exception for cleanup failures."""
    pass


def setup_logging() -> logging.Logger:
    """
    Configure centralized logging for the cleanup process.
    
    Returns:
        Logger instance configured with file and console handlers
    """
    LOG_DIR.mkdir(exist_ok=True)
    
    logger = logging.getLogger('cleanup')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_DIR / 'cleanup.log',
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def extract_imports_from_file(filepath: Path) -> Tuple[Set[str], List[str]]:
    """
    Extract all import statements from a Python file.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        Tuple of (set of imported module names, list of import lines)
    """
    imports = set()
    import_lines = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        raise CodeCleanupError(f"Syntax error in {filepath}: {e}")
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                imports.add(module_name)
                import_lines.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                imports.add(module_name)
                import_lines.append(f"from {node.module} import ...")
    
    return imports, import_lines


def analyze_file_for_cleanup(filepath: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Analyze a single Python file for cleanup opportunities.
    
    Args:
        filepath: Path to the Python file
        logger: Logger instance for reporting
        
    Returns:
        Dictionary with analysis results
    """
    if not filepath.suffix == '.py':
        return {'skipped': True, 'reason': 'Not a Python file'}
    
    results = {
        'path': str(filepath),
        'issues_found': [],
        'lines_analyzed': 0,
        'imports_found': [],
        'cleanup_actions': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = ''.join(lines)
        
        results['lines_analyzed'] = len(lines)
        
        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if TODO_PATTERN.search(line):
                results['issues_found'].append({
                    'type': 'todo_comment',
                    'line': i,
                    'content': line.strip(),
                    'action': 'Remove or resolve TODO'
                })
            
            if DEBUG_PATTERN.search(line):
                results['issues_found'].append({
                    'type': 'debug_artifact',
                    'line': i,
                    'content': line.strip(),
                    'action': 'Remove debug code'
                })
            
            if DEAD_CODE_PATTERN.search(line):
                results['issues_found'].append({
                    'type': 'dead_code',
                    'line': i,
                    'content': line.strip(),
                    'action': 'Remove dead code'
                })
        
        # Analyze imports
        imports, import_lines = extract_imports_from_file(filepath)
        results['imports_found'] = list(imports)
        
        # Check for potentially unused standard library imports
        for imp in imports:
            if imp in COMMON_UNUSED_IMPORTS:
                # Simple heuristic: check if import is used in file
                if content.count(imp) == content.count(f"import {imp}") + content.count(f"from {imp}"):
                    results['issues_found'].append({
                        'type': 'potentially_unused_import',
                        'line': 'N/A',
                        'content': f"import {imp}",
                        'action': 'Verify usage and remove if unused'
                    })
        
        # Check docstring formatting
        if not content.strip().startswith('"""') and not content.strip().startswith("'''"):
            # Module-level docstring check
            try:
                tree = ast.parse(content)
                if ast.get_docstring(tree):
                    docstring = ast.get_docstring(tree)
                    if not docstring.strip().endswith('.'):
                        results['issues_found'].append({
                            'type': 'docstring_format',
                            'line': 'N/A',
                            'content': 'Module docstring',
                            'action': 'Ensure docstring ends with period'
                        })
            except SyntaxError:
                pass
        
        results['cleanup_actions'] = [
            issue['action'] for issue in results['issues_found']
        ]
        
        return results
        
    except Exception as e:
        raise CodeCleanupError(f"Failed to analyze {filepath}: {e}")


def refactor_file(filepath: Path, logger: logging.Logger) -> Dict[str, Any]:
    """
    Perform automated refactoring on a Python file.
    
    Args:
        filepath: Path to the Python file
        logger: Logger instance for reporting
        
    Returns:
        Dictionary with refactoring results
    """
    results = {
        'path': str(filepath),
        'actions_taken': [],
        'errors': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Remove TODO/FIXME comments (replace with resolved note if needed)
        if TODO_PATTERN.search(content):
            content = TODO_PATTERN.sub('', content)
            results['actions_taken'].append('Removed TODO/FIXME comments')
            modified = True
        
        # Remove debug artifacts
        if DEBUG_PATTERN.search(content):
            content = DEBUG_PATTERN.sub('', content)
            results['actions_taken'].append('Removed debug code (print/pdb)')
            modified = True
        
        # Remove dead code blocks
        if DEAD_CODE_PATTERN.search(content):
            content = DEAD_CODE_PATTERN.sub('', content)
            results['actions_taken'].append('Removed dead code blocks')
            modified = True
        
        # Normalize logging imports
        if 'import logging' not in content and 'logging' in content:
            content = 'import logging\n' + content
            results['actions_taken'].append('Added missing logging import')
            modified = True
        
        # Ensure consistent line endings
        content = content.replace('\r\n', '\n')
        
        # Write back if modified
        if modified and content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Refactored {filepath}: {', '.join(results['actions_taken'])}")
        else:
            results['actions_taken'].append('No changes needed')
        
        return results
        
    except Exception as e:
        error_msg = f"Failed to refactor {filepath}: {e}"
        results['errors'].append(error_msg)
        logger.error(error_msg)
        return results


def run_cleanup(logger: logging.Logger) -> Dict[str, Any]:
    """
    Run the full cleanup and refactoring process on the codebase.
    
    Args:
        logger: Logger instance for reporting
        
    Returns:
        Summary of cleanup operations
    """
    summary = {
        'files_processed': 0,
        'files_refactored': 0,
        'total_issues_found': 0,
        'issues_by_type': {},
        'errors': []
    }
    
    logger.info("Starting code cleanup and refactoring...")
    
    # Process all Python files in code/
    python_files = list(CODE_DIR.rglob('*.py'))
    
    if not python_files:
        logger.warning(f"No Python files found in {CODE_DIR}")
        return summary
    
    logger.info(f"Found {len(python_files)} Python files to process")
    
    for filepath in python_files:
        try:
            summary['files_processed'] += 1
            
            # Analyze
            analysis = analyze_file_for_cleanup(filepath, logger)
            if analysis.get('skipped'):
                continue
            
            # Aggregate issues
            for issue in analysis.get('issues_found', []):
                issue_type = issue['type']
                summary['total_issues_found'] += 1
                summary['issues_by_type'][issue_type] = \
                    summary['issues_by_type'].get(issue_type, 0) + 1
            
            # Refactor
            refactoring = refactor_file(filepath, logger)
            if refactoring.get('actions_taken') and \
               refactoring['actions_taken'] != ['No changes needed']:
                summary['files_refactored'] += 1
            
            if refactoring.get('errors'):
                summary['errors'].extend(refactoring['errors'])
                
        except CodeCleanupError as e:
            logger.error(str(e))
            summary['errors'].append(str(e))
        except Exception as e:
            error_msg = f"Unexpected error processing {filepath}: {e}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
    
    logger.info(f"Cleanup complete: {summary['files_processed']} files processed, "
               f"{summary['files_refactored']} refactored, "
               f"{summary['total_issues_found']} issues found")
    
    return summary


def validate_apis(logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate that all public APIs match their documented signatures.
    
    Args:
        logger: Logger instance for reporting
        
    Returns:
        Validation results
    """
    validation_results = {
        'files_checked': 0,
        'api_mismatches': [],
        'errors': []
    }
    
    # Define expected public APIs from the project specification
    expected_apis = {
        'code/analyze_pvalues.py': [
            'generate_permutation_reference',
            'calculate_ks_statistic',
            'main'
        ],
        'code/bootstrap_ci.py': [
            'calculate_bootstrap_ci',
            'load_trajectory_data',
            'run_bootstrap_analysis',
            'main'
        ],
        'code/collect_pvalues.py': [
            'collect_pvalues',
            'aggregate_pvalues'
        ],
        'code/generate_data.py': [
            'generate_correlated_data',
            'generate_distribution_violations',
            'write_dataset_metadata',
            'main'
        ],
        'code/integrate_pipeline.py': [
            'load_simulation_configs',
            'run_integration_pipeline',
            'main'
        ],
        'code/plot_qq.py': [
            'load_pvalue_trajectories',
            'aggregate_pvalues',
            'generate_qq_plot',
            'main'
        ],
        'code/run_tests.py': [
            'run_hypothesis_tests',
            'run_hypothesis_tests_batch',
            'main'
        ],
        'code/sensitivity_analysis.py': [
            'load_trajectories_for_rho',
            'calculate_ks_statistic_for_rho',
            'run_sensitivity_analysis',
            'main'
        ],
        'code/utils/exceptions.py': [
            'HighDimensionalInstabilityError',
            'SimulationError',
            'DataGenerationError',
            'HypothesisTestError',
            'AnalysisError'
        ],
        'code/utils/regularization.py': [
            'is_condition_number_acceptable',
            'regularize_covariance'
        ],
        'code/utils/simulation.py': [
            'SimulationConfig',
            'SyntheticDataset',
            'SimulationOrchestrator',
            'main'
        ]
    }
    
    for relative_path, expected_names in expected_apis.items():
        filepath = PROJECT_ROOT / relative_path
        validation_results['files_checked'] += 1
        
        if not filepath.exists():
            validation_results['api_mismatches'].append({
                'file': relative_path,
                'issue': 'File not found',
                'expected': expected_names,
                'found': []
            })
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            actual_names = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                    # Check if it's public (not starting with _)
                    if not node.name.startswith('_'):
                        actual_names.add(node.name)
                
                # Also check __all__ if present
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            if isinstance(node.value, ast.List):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant):
                                        actual_names.add(elt.value)
            
            missing = set(expected_names) - actual_names
            if missing:
                validation_results['api_mismatches'].append({
                    'file': relative_path,
                    'issue': 'Missing expected public APIs',
                    'expected': expected_names,
                    'found': list(actual_names),
                    'missing': list(missing)
                })
            
        except SyntaxError as e:
            validation_results['api_mismatches'].append({
                'file': relative_path,
                'issue': f'Syntax error: {e}',
                'expected': expected_names,
                'found': []
            })
        except Exception as e:
            validation_results['errors'].append(f"Error validating {relative_path}: {e}")
    
    return validation_results


def main():
    """Main entry point for the cleanup and refactoring script."""
    logger = setup_logging()
    
    try:
        # Run cleanup
        cleanup_summary = run_cleanup(logger)
        
        # Validate APIs
        api_validation = validate_apis(logger)
        
        # Output summary
        logger.info("=" * 60)
        logger.info("CLEANUP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files processed: {cleanup_summary['files_processed']}")
        logger.info(f"Files refactored: {cleanup_summary['files_refactored']}")
        logger.info(f"Total issues found: {cleanup_summary['total_issues_found']}")
        
        if cleanup_summary['issues_by_type']:
            logger.info("Issues by type:")
            for issue_type, count in cleanup_summary['issues_by_type'].items():
                logger.info(f"  - {issue_type}: {count}")
        
        if cleanup_summary['errors']:
            logger.warning(f"Errors encountered: {len(cleanup_summary['errors'])}")
            for error in cleanup_summary['errors']:
                logger.warning(f"  - {error}")
        
        logger.info("=" * 60)
        logger.info("API VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files checked: {api_validation['files_checked']}")
        
        if api_validation['api_mismatches']:
            logger.warning(f"API mismatches found: {len(api_validation['api_mismatches'])}")
            for mismatch in api_validation['api_mismatches']:
                logger.warning(f"  - {mismatch['file']}: {mismatch['issue']}")
                if 'missing' in mismatch:
                    logger.warning(f"    Missing: {mismatch['missing']}")
        else:
            logger.info("All APIs validated successfully!")
        
        if api_validation['errors']:
            logger.error(f"Validation errors: {len(api_validation['errors'])}")
            for error in api_validation['errors']:
                logger.error(f"  - {error}")
        
        # Return exit code based on errors
        if cleanup_summary['errors'] or api_validation['errors']:
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"Fatal error during cleanup: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
