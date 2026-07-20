"""
Utility functions for code cleanup and refactoring.
This module provides helpers for standardizing imports, removing dead code markers,
and ensuring consistent formatting across the codebase.
"""
import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Standard imports that should be grouped together
STANDARD_IMPORTS = {
    'os', 'sys', 'json', 'pickle', 're', 'math', 'random', 'logging',
    'pathlib', 'typing', 'collections', 'itertools', 'functools', 'dataclasses',
    'numpy', 'pandas', 'sklearn', 'pytest', 'yaml', 'yaml'
}

# Patterns to detect TODO/FIXME markers
TODO_PATTERN = re.compile(r'#\s*(TODO|FIXME|XXX|HACK):', re.IGNORECASE)
PLACEHOLDER_PATTERN = re.compile(r'pass\s*$', re.MULTILINE)

def find_python_files(root_dir: str) -> List[Path]:
    """Find all Python files in the given directory recursively."""
    root_path = Path(root_dir)
    return list(root_path.rglob('*.py'))

def check_for_todos(file_path: Path) -> List[Dict[str, any]]:
    """Check a file for TODO, FIXME, XXX, HACK markers."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                match = TODO_PATTERN.search(line)
                if match:
                    issues.append({
                        'file': str(file_path),
                        'line': i,
                        'type': match.group(1).upper(),
                        'content': line.strip()
                    })
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    return issues

def check_for_pass_only_functions(file_path: Path) -> List[Dict[str, any]]:
    """Check for functions that only contain 'pass'."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if (len(node.body) == 1 and 
                        isinstance(node.body[0], ast.Pass)):
                        issues.append({
                            'file': str(file_path),
                            'line': node.lineno,
                            'type': 'PASS_ONLY_FUNCTION',
                            'function_name': node.name
                        })
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
    return issues

def check_import_groups(file_path: Path) -> List[Dict[str, any]]:
    """Check if imports are properly grouped (stdlib, third-party, local)."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        current_group = None
        last_import_line = -1
        group_order = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                # Determine group
                if stripped.startswith('from __future__'):
                    continue
                
                module = stripped.split()[1].split('.')[0] if ' ' in stripped else stripped.split(' ')[0].replace('import ', '')
                
                if module in STANDARD_IMPORTS:
                    group = 'stdlib'
                elif module.startswith(('sklearn', 'numpy', 'pandas', 'pytest', 'yaml', 'torch', 'tensorflow')):
                    group = 'third_party'
                else:
                    group = 'local'
                
                # Check for proper grouping
                if current_group is not None and group != current_group:
                    if group_order and group_order[-1] == group:
                        # Same group appeared again after a different one - issue
                        issues.append({
                            'file': str(file_path),
                            'line': i + 1,
                            'type': 'IMPORT_GROUPING',
                            'message': f"Import group '{group}' appears after '{current_group}' without proper separation"
                        })
                    group_order.append(group)
                
                current_group = group
                last_import_line = i + 1
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error checking imports in {file_path}: {e}")
    return issues

def analyze_code_quality(project_root: str = 'code') -> Dict[str, any]:
    """Perform a comprehensive code quality analysis."""
    results = {
        'total_files': 0,
        'todo_count': 0,
        'pass_only_functions': 0,
        'import_issues': 0,
        'files_with_issues': set(),
        'details': []
    }
    
    py_files = find_python_files(project_root)
    results['total_files'] = len(py_files)
    
    for file_path in py_files:
        rel_path = str(file_path.relative_to(Path(project_root).parent))
        
        # Check for TODOs
        todos = check_for_todos(file_path)
        if todos:
            results['todo_count'] += len(todos)
            results['files_with_issues'].add(rel_path)
            results['details'].extend(todos)
        
        # Check for pass-only functions
        pass_issues = check_for_pass_only_functions(file_path)
        if pass_issues:
            results['pass_only_functions'] += len(pass_issues)
            results['files_with_issues'].add(rel_path)
            results['details'].extend(pass_issues)
        
        # Check import grouping
        import_issues = check_import_groups(file_path)
        if import_issues:
            results['import_issues'] += len(import_issues)
            results['files_with_issues'].add(rel_path)
            results['details'].extend(import_issues)
    
    results['files_with_issues'] = list(results['files_with_issues'])
    return results

def generate_cleanup_report(results: Dict[str, any]) -> str:
    """Generate a human-readable cleanup report."""
    report_lines = [
        "=" * 60,
        "CODE CLEANUP AND REFACTORING REPORT",
        "=" * 60,
        f"Total Python files analyzed: {results['total_files']}",
        f"Files with issues: {len(results['files_with_issues'])}",
        "",
        "SUMMARY:",
        f"  - TODO/FIXME/XXX/HACK markers: {results['todo_count']}",
        f"  - Pass-only functions: {results['pass_only_functions']}",
        f"  - Import grouping issues: {results['import_issues']}",
        "",
        "FILES REQUIRING ATTENTION:",
    ]
    
    for file_path in sorted(results['files_with_issues']):
        report_lines.append(f"  - {file_path}")
    
    if results['details']:
        report_lines.append("")
        report_lines.append("DETAILED ISSUES:")
        for detail in results['details']:
            report_lines.append(f"  [{detail.get('type', 'UNKNOWN')}] {detail['file']}:{detail.get('line', '?')}")
            if 'content' in detail:
                report_lines.append(f"      {detail['content']}")
            if 'message' in detail:
                report_lines.append(f"      {detail['message']}")
            if 'function_name' in detail:
                report_lines.append(f"      Function: {detail['function_name']}")
    
    report_lines.append("")
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)

def main():
    """Main entry point for code cleanup analysis."""
    logger.info("Starting code cleanup and refactoring analysis...")
    
    # Analyze the code directory
    results = analyze_code_quality('code')
    
    # Generate and print report
    report = generate_cleanup_report(results)
    print(report)
    
    # Also save to a file
    output_path = Path('data/processed/cleanup_report.txt')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Cleanup report saved to {output_path}")
    
    # Return summary for programmatic use
    return {
        'total_files': results['total_files'],
        'issues_found': len(results['files_with_issues']),
        'todo_count': results['todo_count'],
        'pass_only_functions': results['pass_only_functions'],
        'import_issues': results['import_issues']
    }

if __name__ == '__main__':
    main()