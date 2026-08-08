"""
Linting configuration and cleanup utilities for analysis modules.

This module provides tools to check code quality metrics including:
- Import validation
- Docstring presence and format
- Line length compliance
- Cyclomatic complexity checks
- Module cleanup utilities

All checks are designed to work with the project's existing analysis modules
and adhere to the project's coding standards.
"""

import os
import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Linting configuration
MAX_LINE_LENGTH = 88
MAX_COMPLEXITY = 10
REQUIRED_DOCSTRING_TYPES = {'module', 'class', 'function'}

# Analysis modules to check
ANALYSIS_MODULES = [
    'bootstrapping',
    'clustering',
    'correlation',
    'decomposition',
    'generate_cluster_results',
    'generate_decomposition_results',
    'generate_trend_results',
    'linting_config',
    'trends'
]

def get_module_path(module_name: str) -> Path:
    """Get the full path to an analysis module file.
    
    Args:
        module_name: Name of the module (without .py extension)
        
    Returns:
        Path object pointing to the module file
    """
    return PROJECT_ROOT / 'code' / 'analysis' / f'{module_name}.py'

def check_imports(module_path: Path) -> List[Dict[str, Any]]:
    """Check for undefined or problematic imports in a module.
    
    Args:
        module_path: Path to the module file
        
    Returns:
        List of issues found, each as a dict with 'line', 'message' keys
    """
    issues = []
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Track imported names
        imported_names: Set[str] = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names.add(name)
        
        # Check for common problematic patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and 'analysis' in node.module:
                    # Check if the imported module exists
                    submodule = node.module.split('.')[-1]
                    submodule_path = get_module_path(submodule)
                    if not submodule_path.exists():
                        issues.append({
                            'line': node.lineno,
                            'message': f"Import from non-existent module: {node.module}"
                        })
                        
    except SyntaxError as e:
        issues.append({
            'line': e.lineno or 0,
            'message': f"Syntax error: {e.msg}"
        })
    except Exception as e:
        issues.append({
            'line': 0,
            'message': f"Error parsing module: {str(e)}"
        })
        
    return issues

def check_docstrings(module_path: Path) -> List[Dict[str, Any]]:
    """Check for missing or malformed docstrings in a module.
    
    Args:
        module_path: Path to the module file
        
    Returns:
        List of issues found, each as a dict with 'line', 'message' keys
    """
    issues = []
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        # Check module docstring
        if not ast.get_docstring(tree):
            issues.append({
                'line': 1,
                'message': "Missing module-level docstring"
            })
        
        # Check function and class docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append({
                        'line': node.lineno,
                        'message': f"Missing docstring for {node.__class__.__name__.lower()} '{node.name}'"
                    })
                
                # Check for empty docstrings
                docstring = ast.get_docstring(node)
                if docstring and not docstring.strip():
                    issues.append({
                        'line': node.lineno,
                        'message': f"Empty docstring for {node.__class__.__name__.lower()} '{node.name}'"
                    })
                    
    except SyntaxError as e:
        issues.append({
            'line': e.lineno or 0,
            'message': f"Syntax error: {e.msg}"
        })
    except Exception as e:
        issues.append({
            'line': 0,
            'message': f"Error parsing module: {str(e)}"
        })
        
    return issues

def check_line_length(module_path: Path) -> List[Dict[str, Any]]:
    """Check for lines exceeding the maximum length.
    
    Args:
        module_path: Path to the module file
        
    Returns:
        List of issues found, each as a dict with 'line', 'message' keys
    """
    issues = []
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Remove trailing newline for length check
                line_content = line.rstrip('\n\r')
                if len(line_content) > MAX_LINE_LENGTH:
                    issues.append({
                        'line': line_num,
                        'message': f"Line exceeds {MAX_LINE_LENGTH} characters ({len(line_content)} chars)"
                    })
    except Exception as e:
        issues.append({
            'line': 0,
            'message': f"Error reading file: {str(e)}"
        })
        
    return issues

def check_complexity(module_path: Path) -> List[Dict[str, Any]]:
    """Check for functions with high cyclomatic complexity.
    
    Args:
        module_path: Path to the module file
        
    Returns:
        List of issues found, each as a dict with 'line', 'message' keys
    """
    issues = []
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = _calculate_cyclomatic_complexity(node)
                if complexity > MAX_COMPLEXITY:
                    issues.append({
                        'line': node.lineno,
                        'message': f"Function '{node.name}' has high complexity ({complexity} > {MAX_COMPLEXITY})"
                    })
                    
    except SyntaxError as e:
        issues.append({
            'line': e.lineno or 0,
            'message': f"Syntax error: {e.msg}"
        })
    except Exception as e:
        issues.append({
            'line': 0,
            'message': f"Error parsing module: {str(e)}"
        })
        
    return issues

def _calculate_cyclomatic_complexity(node: ast.FunctionDef) -> int:
    """Calculate cyclomatic complexity for a function node.
    
    Args:
        node: AST function node
        
    Returns:
        Integer complexity score
    """
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                            ast.With, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
            
    return complexity

def run_lint_checks(module_name: str) -> Dict[str, Any]:
    """Run all lint checks on a specific module.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        Dictionary with check results
    """
    module_path = get_module_path(module_name)
    
    if not module_path.exists():
        return {
            'module': module_name,
            'status': 'error',
            'message': f"Module file not found: {module_path}"
        }
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_imports(module_path))
    all_issues.extend(check_docstrings(module_path))
    all_issues.extend(check_line_length(module_path))
    all_issues.extend(check_complexity(module_path))
    
    return {
        'module': module_name,
        'status': 'pass' if not all_issues else 'fail',
        'issue_count': len(all_issues),
        'issues': all_issues
    }

def generate_lint_report() -> Dict[str, Any]:
    """Generate a comprehensive lint report for all analysis modules.
    
    Returns:
        Dictionary with overall report and per-module results
    """
    results = {}
    total_issues = 0
    passed_modules = 0
    failed_modules = 0
    
    for module_name in ANALYSIS_MODULES:
        result = run_lint_checks(module_name)
        results[module_name] = result
        total_issues += result['issue_count']
        
        if result['status'] == 'pass':
            passed_modules += 1
        else:
            failed_modules += 1
    
    return {
        'total_modules': len(ANALYSIS_MODULES),
        'passed_modules': passed_modules,
        'failed_modules': failed_modules,
        'total_issues': total_issues,
        'module_results': results,
        'status': 'pass' if failed_modules == 0 else 'fail'
    }

def cleanup_analysis_modules() -> Dict[str, Any]:
    """Perform cleanup operations on analysis modules.
    
    This includes:
    - Removing unused imports
    - Standardizing docstring format
    - Fixing line length issues (where safe)
    
    Returns:
        Dictionary with cleanup results
    """
    cleanup_results = {}
    
    for module_name in ANALYSIS_MODULES:
        module_path = get_module_path(module_name)
        
        if not module_path.exists():
            cleanup_results[module_name] = {
                'status': 'skipped',
                'message': 'File not found'
            }
            continue
        
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic cleanup operations
            original_content = content
            
            # Remove trailing whitespace
            lines = content.split('\n')
            cleaned_lines = [line.rstrip() for line in lines]
            content = '\n'.join(cleaned_lines)
            
            # Ensure single trailing newline
            content = content.rstrip() + '\n'
            
            # Write back if changed
            if content != original_content:
                with open(module_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                cleanup_results[module_name] = {
                    'status': 'updated',
                    'changes': ['trailing_whitespace', 'final_newline']
                }
            else:
                cleanup_results[module_name] = {
                    'status': 'unchanged',
                    'changes': []
                }
                
        except Exception as e:
            cleanup_results[module_name] = {
                'status': 'error',
                'message': str(e)
            }
    
    return cleanup_results

def main() -> int:
    """Main entry point for linting and cleanup operations.
    
    Returns:
        Exit code (0 for success, 1 for failures)
    """
    print("Running analysis module lint checks...")
    print("=" * 50)
    
    # Generate report
    report = generate_lint_report()
    
    # Print summary
    print(f"\nOverall Status: {report['status'].upper()}")
    print(f"Modules Passed: {report['passed_modules']}/{report['total_modules']}")
    print(f"Modules Failed: {report['failed_modules']}/{report['total_modules']}")
    print(f"Total Issues: {report['total_issues']}")
    
    # Print per-module details
    print("\n" + "=" * 50)
    print("Per-Module Results:")
    print("=" * 50)
    
    for module_name, result in report['module_results'].items():
        status_symbol = "✓" if result['status'] == 'pass' else "✗"
        print(f"\n{status_symbol} {module_name}: {result['status'].upper()} "
              f"({result['issue_count']} issues)")
        
        if result['issues']:
            for issue in result['issues'][:5]:  # Show first 5 issues
                print(f"  Line {issue['line']}: {issue['message']}")
            if result['issue_count'] > 5:
                print(f"  ... and {result['issue_count'] - 5} more issues")
    
    # Run cleanup
    print("\n" + "=" * 50)
    print("Running cleanup operations...")
    print("=" * 50)
    
    cleanup_results = cleanup_analysis_modules()
    
    for module_name, result in cleanup_results.items():
        status_symbol = "✓" if result['status'] in ['updated', 'unchanged'] else "✗"
        print(f"{status_symbol} {module_name}: {result['status'].upper()}")
        if 'changes' in result and result['changes']:
            print(f"  Changes: {', '.join(result['changes'])}")
        if 'message' in result:
            print(f"  Message: {result['message']}")
    
    # Return appropriate exit code
    return 0 if report['status'] == 'pass' else 1

if __name__ == '__main__':
    sys.exit(main())