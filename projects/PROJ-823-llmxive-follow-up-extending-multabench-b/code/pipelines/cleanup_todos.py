"""
Pipeline to scan the codebase for TODO, FIXME, HACK, and XXX comments
related to US1, US2, and US3 implementations and generate a cleanup report.
This task (T052) ensures all open issues and TODOs are identified and addressed.
"""
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Configuration
TODO_PATTERNS = [
    r'#\s*TODO[:\s]*(.*)',
    r'#\s*FIXME[:\s]*(.*)',
    r'#\s*HACK[:\s]*(.*)',
    r'#\s*XXX[:\s]*(.*)',
    r'#\s*NOTE[:\s]*(.*)'  # Sometimes notes indicate unresolved issues
]

COMPILE = re.compile('|'.join(TODO_PATTERNS), re.IGNORECASE)

# Directories to scan (excluding tests and virtual envs)
EXCLUDE_DIRS = {
    'venv', '.venv', '__pycache__', '.git', 'node_modules', 
    '.pytest_cache', '.mypy_cache', 'build', 'dist', 'htmlcov'
}

# File extensions to scan
SCAN_EXTENSIONS = {'.py', '.md', '.yaml', '.yml', '.txt', '.sh'}

def scan_file_for_todos(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a single file for TODO comments.
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        List of dictionaries containing TODO details
    """
    todos = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            match = COMPILE.search(line)
            if match:
                # Extract the comment text
                comment_text = match.group(0).split(':', 1)[-1].strip()
                if not comment_text:
                    comment_text = match.group(1).strip() if match.lastindex else "No description"
                
                todos.append({
                    'file': str(file_path),
                    'line': line_num,
                    'type': match.group(0).split(':')[0].strip().lstrip('#').strip(),
                    'description': comment_text,
                    'full_line': line.strip()
                })
    except Exception as e:
        # Log error but continue scanning other files
        print(f"Error scanning {file_path}: {e}")
        
    return todos

def scan_directory(root_path: Path) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for TODO comments.
    
    Args:
        root_path: Root directory to scan
        
    Returns:
        List of all TODOs found
    """
    all_todos = []
    
    for file_path in root_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in SCAN_EXTENSIONS:
            # Check if any parent directory is excluded
            excluded = False
            for part in file_path.parts:
                if part in EXCLUDE_DIRS:
                    excluded = True
                    break
            
            if not excluded:
                todos = scan_file_for_todos(file_path)
                all_todos.extend(todos)
                
    return all_todos

def generate_report(todos: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Generate a comprehensive report of all TODOs found.
    
    Args:
        todos: List of all TODOs found
        output_path: Path to save the report
        
    Returns:
        Summary statistics of the report
    """
    # Group by type
    by_type = {}
    by_file = {}
    
    for todo in todos:
        # Group by type
        todo_type = todo['type']
        if todo_type not in by_type:
            by_type[todo_type] = []
        by_type[todo_type].append(todo)
        
        # Group by file
        file_path = todo['file']
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(todo)
    
    # Create report structure
    report = {
        'scan_timestamp': datetime.now().isoformat(),
        'total_todos': len(todos),
        'files_scanned': len(by_file),
        'summary_by_type': {k: len(v) for k, v in by_type.items()},
        'todos_by_file': {k: len(v) for k, v in by_file.items()},
        'details': todos,
        'recommendations': []
    }
    
    # Generate recommendations
    if 'TODO' in by_type:
        report['recommendations'].append(
            f"Found {len(by_type['TODO'])} TODOs. Consider resolving these before final release."
        )
    if 'FIXME' in by_type:
        report['recommendations'].append(
            f"Found {len(by_type['FIXME'])} FIXMEs. These indicate known bugs that need immediate attention."
        )
    if 'HACK' in by_type:
        report['recommendations'].append(
            f"Found {len(by_type['HACK'])} HACKs. These temporary solutions should be refactored."
        )
        
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    # Also generate a human-readable markdown summary
    md_path = output_path.with_suffix('.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# TODO/FIXME/HACK Scan Report\n\n")
        f.write(f"**Generated:** {report['scan_timestamp']}\n\n")
        f.write(f"**Total Issues Found:** {report['total_todos']}\n")
        f.write(f"**Files Scanned:** {report['files_scanned']}\n\n")
        
        f.write("## Summary by Type\n\n")
        for todo_type, count in report['summary_by_type'].items():
            f.write(f"- **{todo_type}**: {count}\n")
        f.write("\n")
        
        f.write("## Detailed List\n\n")
        for todo in todos:
            f.write(f"### [{todo['type']}] {todo['file']}:{todo['line']}\n")
            f.write(f"**Description:** {todo['description']}\n")
            f.write(f"**Code:** `{todo['full_line']}`\n\n")
            
        if report['recommendations']:
            f.write("## Recommendations\n\n")
            for rec in report['recommendations']:
                f.write(f"- {rec}\n")
                
    return report

def main():
    """Main entry point for the cleanup_todos pipeline."""
    parser = argparse.ArgumentParser(
        description='Scan codebase for TODOs and generate cleanup report (T052)'
    )
    parser.add_argument(
        '--root',
        type=str,
        default='.',
        help='Root directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/artifacts/todo_cleanup_report.json',
        help='Output path for the JSON report (default: data/artifacts/todo_cleanup_report.json)'
    )
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    output_path = Path(args.output)
    
    print(f"Scanning directory: {root_path}")
    todos = scan_directory(root_path)
    
    print(f"Found {len(todos)} TODOs/FIXMEs/HACKs")
    report = generate_report(todos, output_path)
    
    print(f"Report saved to: {output_path}")
    print(f"Markdown summary saved to: {output_path.with_suffix('.md')}")
    
    # Print summary
    print("\n--- Summary ---")
    print(f"Total issues: {report['total_todos']}")
    for todo_type, count in report['summary_by_type'].items():
        print(f"  {todo_type}: {count}")
        
    if report['recommendations']:
        print("\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

if __name__ == '__main__':
    main()
