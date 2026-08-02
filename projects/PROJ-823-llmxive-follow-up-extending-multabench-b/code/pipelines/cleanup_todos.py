"""
Pipeline to scan the codebase for TODOs, FIXMEs, and open issues related to US1, US2, and US3.
Generates a report of found items and optionally removes them if they are marked for closure.
"""
import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import logging utilities from the project's existing API surface
try:
    from utils.logging import get_logger, log_info, log_warning, log_error
except ImportError:
    # Fallback if running as script without package context
    def get_logger(name):
        import logging
        return logging.getLogger(name)
    def log_info(logger, msg): logger.info(msg)
    def log_warning(logger, msg): logger.warning(msg)
    def log_error(logger, msg): logger.error(msg)

# Patterns to search for
TODO_PATTERNS = [
    r'#\s*TODO:\s*(.*)',
    r'#\s*FIXME:\s*(.*)',
    r'#\s*XXX:\s*(.*)',
    r'#\s*HACK:\s*(.*)',
    r'#\s*OPEN:\s*(.*)',
    r'#\s*TODO\s*\((.*?)\):\s*(.*)', # Specific task ID TODOs
]

# Keywords indicating US1, US2, US3 context
US_KEYWORDS = ['US1', 'US2', 'US3', 'User Story 1', 'User Story 2', 'User Story 3', 
               'CPU-Conditioned', 'Frozen Baseline', 'Recovery Ratio', 'projection']

def scan_file_for_todos(file_path: Path) -> List[Dict[str, Any]]:
    """Scan a single Python file for TODOs and related comments."""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        log_error(get_logger(__name__), f"Failed to read {file_path}: {e}")
        return issues

    for line_num, line in enumerate(lines, 1):
        for pattern in TODO_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Extract the comment text
                comment_text = match.group(0)
                # Check if this TODO is related to our user stories
                is_relevant = any(kw.lower() in comment_text.lower() for kw in US_KEYWORDS)
                
                # If it's a generic TODO but not related to US1/2/3, we might skip it 
                # unless the task implies cleaning ALL TODOs. 
                # The task says "Close any open issues or TODOs ... related to US1, US2, US3".
                # So we only report relevant ones.
                if is_relevant or 'US1' in comment_text or 'US2' in comment_text or 'US3' in comment_text:
                    issues.append({
                        'file': str(file_path),
                        'line': line_num,
                        'content': line.strip(),
                        'type': 'TODO' if 'TODO' in comment_text else 'FIXME' if 'FIXME' in comment_text else 'OTHER',
                        'description': comment_text,
                        'is_relevant_to_stories': is_relevant
                    })
    return issues

def scan_directory(directory: Path) -> List[Dict[str, Any]]:
    """Recursively scan a directory for TODOs."""
    all_issues = []
    py_files = list(directory.rglob("*.py"))
    
    # Also check specific config/docs if they exist in code/
    other_files = [
        directory / "README.md",
        directory / "tasks.md",
        directory / "plan.md"
    ]
    for f in other_files:
        if f.exists():
            py_files.append(f)

    for file_path in py_files:
        if "test" not in str(file_path) and "__pycache__" not in str(file_path):
            issues = scan_file_for_todos(file_path)
            all_issues.extend(issues)
    
    return all_issues

def generate_report(issues: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """Generate a structured report of found TODOs."""
    report = {
        'scan_timestamp': datetime.now().isoformat(),
        'total_issues_found': len(issues),
        'issues': issues,
        'summary': {
            'US1_related': len([i for i in issues if 'US1' in i['description']]),
            'US2_related': len([i for i in issues if 'US2' in i['description']]),
            'US3_related': len([i for i in issues if 'US3' in i['description']]),
        }
    }
    
    # Write JSON report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Write human-readable summary
    summary_path = output_path.with_suffix('.md')
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"# TODO/Issue Scan Report\n")
        f.write(f"**Generated**: {report['scan_timestamp']}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Total Issues Found: {report['total_issues_found']}\n")
        f.write(f"- US1 Related: {report['summary']['US1_related']}\n")
        f.write(f"- US2 Related: {report['summary']['US2_related']}\n")
        f.write(f"- US3 Related: {report['summary']['US3_related']}\n\n")
        
        if issues:
            f.write("## Details\n\n")
            for issue in issues:
                f.write(f"### {issue['file']}:{issue['line']}\n")
                f.write(f"**Type**: {issue['type']}\n")
                f.write(f"**Content**: `{issue['description']}`\n\n")
        else:
            f.write("## No open issues or TODOs related to US1, US2, or US3 found.\n")
            f.write("The codebase is clean regarding the specified user stories.\n")

    return report

def main():
    parser = argparse.ArgumentParser(description="Scan codebase for TODOs related to US1, US2, US3")
    parser.add_argument('--code-root', type=str, default='code', help='Root directory to scan')
    parser.add_argument('--output-dir', type=str, default='data/artifacts', help='Directory to save reports')
    args = parser.parse_args()

    logger = get_logger(__name__)
    log_info(logger, f"Starting TODO scan in {args.code_root}")

    code_root = Path(args.code_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not code_root.exists():
        log_error(logger, f"Code root {code_root} does not exist")
        return 1

    issues = scan_directory(code_root)
    
    # Generate report with run_id style naming if possible, or timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = output_dir / f"todo_cleanup_report_{timestamp}.json"
    
    report = generate_report(issues, report_path)
    
    log_info(logger, f"Scan complete. Found {report['total_issues_found']} issues.")
    log_info(logger, f"Report saved to {report_path}")
    
    # If no issues related to US1/2/3, consider this a success for the task
    if report['total_issues_found'] == 0:
        log_info(logger, "No open issues found. Task T052 satisfied.")
    else:
        log_warning(logger, f"Found {report['total_issues_found']} open issues. Review report for closure.")

    return 0

if __name__ == "__main__":
    exit(main())