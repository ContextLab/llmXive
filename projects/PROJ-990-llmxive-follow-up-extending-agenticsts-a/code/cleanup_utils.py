"""
Code cleanup utilities for analyzing Python code quality.
Implements checks for TODOs, pass-only functions, import grouping, and general quality metrics.
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

def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the given directory recursively."""
    return list(root_dir.rglob('*.py'))

def check_for_todos(tree: ast.AST, file_path: Path) -> List[Dict]:
    """Check for TODO, FIXME, XXX, and HACK comments in the AST."""
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            # Check for string literals that might be comments (though AST doesn't capture comments directly)
            # We'll use a regex on the source code instead for reliable comment detection
            pass
    
    # Fallback to regex on source code for comment detection
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return issues

    pattern = re.compile(r'#\s*(TODO|FIXME|XXX|HACK):?\s*(.*)', re.IGNORECASE)
    for i, line in enumerate(lines, 1):
        match = pattern.search(line)
        if match:
            issues.append({
                'file': str(file_path),
                'line': i,
                'type': match.group(1).upper(),
                'message': match.group(2).strip(),
                'code': line.strip()
            })
    return issues

def check_for_pass_only_functions(tree: ast.AST, file_path: Path) -> List[Dict]:
    """Check for functions or classes that contain only 'pass'."""
    issues = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Check if body contains only Pass or Docstring + Pass
            body = node.body
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                issues.append({
                    'file': str(file_path),
                    'line': node.lineno,
                    'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                    'name': node.name,
                    'issue': 'Empty body (only pass)'
                })
            elif len(body) == 2:
                # Check for docstring followed by pass
                if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    if isinstance(body[1], ast.Pass):
                        issues.append({
                            'file': str(file_path),
                            'line': node.lineno,
                            'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                            'name': node.name,
                            'issue': 'Empty body (docstring + pass)'
                        })
    return issues

def check_import_groups(tree: ast.AST, file_path: Path) -> List[Dict]:
    """Check for properly grouped imports (stdlib, third-party, local)."""
    issues = []
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'line': node.lineno,
                    'module': alias.name,
                    'type': 'import'
                })
        elif isinstance(node, ast.ImportFrom):
            imports.append({
                'line': node.lineno,
                'module': node.module or '',
                'type': 'from'
            })

    if not imports:
        return issues

    # Simple heuristic: check if imports are contiguous and grouped
    # This is a simplified check; real grouping is complex
    prev_module = None
    for imp in imports:
        if prev_module is not None:
            # Check if there's a gap
            if imp['line'] - prev_module['line'] > 1:
                # Might be okay if there's a blank line or comment
                pass
        prev_module = imp

    # More robust check: ensure standard library imports come first
    stdlib_modules = {'os', 'sys', 'json', 'logging', 'pathlib', 'typing', 're', 'ast', 'hashlib'}
    stdlib_lines = [imp['line'] for imp in imports if imp['module'] in stdlib_modules]
    third_party_lines = [imp['line'] for imp in imports if imp['module'] not in stdlib_modules and imp['module'] != '']
    
    if stdlib_lines and third_party_lines:
        max_stdlib = max(stdlib_lines)
        min_third_party = min(third_party_lines)
        if max_stdlib > min_third_party:
            issues.append({
                'file': str(file_path),
                'line': min_third_party,
                'type': 'import_grouping',
                'issue': 'Third-party imports appear before standard library imports'
            })

    return issues

def analyze_code_quality(file_path: Path) -> Dict:
    """Perform a comprehensive code quality analysis on a single file."""
    results = {
        'file': str(file_path),
        'todos': [],
        'empty_functions': [],
        'import_issues': [],
        'line_count': 0,
        'complexity': 0
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        results['line_count'] = len(source.splitlines())
        
        tree = ast.parse(source)
        
        # Calculate basic complexity (number of nodes)
        results['complexity'] = len(list(ast.walk(tree)))
        
        results['todos'] = check_for_todos(tree, file_path)
        results['empty_functions'] = check_for_pass_only_functions(tree, file_path)
        results['import_issues'] = check_import_groups(tree, file_path)
        
    except SyntaxError as e:
        results['syntax_error'] = str(e)
        logger.error(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        results['error'] = str(e)
        logger.error(f"Error analyzing {file_path}: {e}")

    return results

def generate_cleanup_report(root_dir: Path) -> Dict:
    """Generate a comprehensive cleanup report for all Python files in the directory."""
    report = {
        'root_directory': str(root_dir),
        'files_analyzed': 0,
        'total_issues': 0,
        'issues_by_type': {
            'todo': 0,
            'empty_function': 0,
            'import_grouping': 0,
            'syntax_error': 0
        },
        'files_with_issues': [],
        'summary': ''
    }

    python_files = find_python_files(root_dir)
    report['files_analyzed'] = len(python_files)
    logger.info(f"Analyzing {len(python_files)} Python files in {root_dir}")

    all_issues = []

    for file_path in python_files:
        analysis = analyze_code_quality(file_path)
        
        if 'syntax_error' in analysis:
            report['issues_by_type']['syntax_error'] += 1
            report['total_issues'] += 1
            report['files_with_issues'].append({
                'file': analysis['file'],
                'issues': [{'type': 'syntax_error', 'message': analysis['syntax_error']}]
            })
            continue

        file_issues = []
        
        if analysis['todos']:
            report['issues_by_type']['todo'] += len(analysis['todos'])
            report['total_issues'] += len(analysis['todos'])
            file_issues.extend([{'type': 'todo', **issue} for issue in analysis['todos']])
        
        if analysis['empty_functions']:
            report['issues_by_type']['empty_function'] += len(analysis['empty_functions'])
            report['total_issues'] += len(analysis['empty_functions'])
            file_issues.extend([{'type': 'empty_function', **issue} for issue in analysis['empty_functions']])
        
        if analysis['import_issues']:
            report['issues_by_type']['import_grouping'] += len(analysis['import_issues'])
            report['total_issues'] += len(analysis['import_issues'])
            file_issues.extend([{'type': 'import_grouping', **issue} for issue in analysis['import_issues']])

        if file_issues:
            report['files_with_issues'].append({
                'file': analysis['file'],
                'issues': file_issues
            })

    # Generate summary
    if report['total_issues'] == 0:
        report['summary'] = "No issues found. Codebase is clean!"
    else:
        report['summary'] = f"Found {report['total_issues']} issues across {len(report['files_with_issues'])} files."
        report['summary'] += f"\n- {report['issues_by_type']['todo']} TODOs/FIXMEs"
        report['summary'] += f"\n- {report['issues_by_type']['empty_function']} empty functions/classes"
        report['summary'] += f"\n- {report['issues_by_type']['import_grouping']} import grouping issues"
        report['summary'] += f"\n- {report['issues_by_type']['syntax_error']} syntax errors"

    return report

def main():
    """Main entry point for the cleanup utility."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze code quality and generate cleanup report')
    parser.add_argument('--root', '-r', type=Path, default=Path('code'), 
                      help='Root directory to analyze (default: code/)')
    parser.add_argument('--output', '-o', type=Path, default=Path('data/processed/cleanup_report.json'),
                      help='Output file for the report (default: data/processed/cleanup_report.json)')
    
    args = parser.parse_args()
    
    if not args.root.exists():
        logger.error(f"Root directory does not exist: {args.root}")
        return 1

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    report = generate_cleanup_report(args.root)
    
    # Save report
    import json
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Cleanup report saved to {args.output}")
    print(report['summary'])
    
    return 0 if report['total_issues'] == 0 else 1

if __name__ == '__main__':
    exit(main())
