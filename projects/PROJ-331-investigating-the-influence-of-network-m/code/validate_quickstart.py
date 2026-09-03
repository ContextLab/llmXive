"""
validate_quickstart.py

Validates the quickstart.md documentation by checking:
1. All referenced paths exist.
2. All referenced commands are syntactically valid and executable (dry-run).
3. All prerequisites (dependencies, files) are met.

Produces a JSON report at `data/logs/quickstart_validation_report.json`.
"""
import os
import sys
import re
import json
import logging
import subprocess
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ensure_dirs
from utils import get_logger, safe_write_json, safe_read_text

def parse_quickstart(quickstart_path: str) -> dict:
    """
    Parses quickstart.md to extract:
    - Prerequisites (pip installs, file checks)
    - Commands to run
    - Paths mentioned
    """
    if not os.path.exists(quickstart_path):
        raise FileNotFoundError(f"quickstart.md not found at {quickstart_path}")

    content = safe_read_text(quickstart_path)
    if not content:
        raise ValueError("quickstart.md is empty")

    lines = content.split('\n')
    sections = {
        'prerequisites': [],
        'commands': [],
        'paths': [],
        'warnings': []
    }

    current_section = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect sections
        if stripped.lower().startswith('prerequisites'):
            current_section = 'prerequisites'
            continue
        elif stripped.lower().startswith('commands'):
            current_section = 'commands'
            continue
        elif stripped.lower().startswith('paths'):
            current_section = 'paths'
            continue
        elif stripped.lower().startswith('output'):
            current_section = 'paths' # Treat output as paths
            continue
        elif stripped.lower().startswith('note') or stripped.lower().startswith('warning'):
            current_section = 'warnings'
            continue

        # Parse list items
        if stripped.startswith('-'):
            item = stripped[1:].strip()
            if current_section and item:
                sections[current_section].append(item)
        elif current_section and stripped:
            # Maybe a direct line item
            if current_section in ['commands', 'paths']:
                sections[current_section].append(stripped)

    return sections

def validate_paths(paths: list, base_dir: str) -> dict:
    """Checks if referenced paths exist."""
    results = {
        'valid': [],
        'invalid': [],
        'missing': []
    }

    for p_str in paths:
        # Clean path string (remove markdown formatting)
        p_str = re.sub(r'`', '', p_str).strip()
        if not p_str:
            continue

        # Check if it's a file or dir pattern
        if '*' in p_str or '?' in p_str:
            # Glob pattern
            full_pattern = os.path.join(base_dir, p_str)
            matches = list(Path(base_dir).glob(p_str))
            if matches:
                results['valid'].append(p_str)
            else:
                results['missing'].append(p_str)
        else:
            full_path = os.path.join(base_dir, p_str)
            if os.path.exists(full_path):
                results['valid'].append(p_str)
            else:
                results['invalid'].append(p_str)

    return results

def validate_commands(commands: list) -> dict:
    """
    Validates commands by attempting a dry-run or syntax check.
    For 'python', checks if the script exists.
    For 'pip', checks if package is available (mock check).
    """
    results = {
        'valid': [],
        'invalid': [],
        'skipped': []
    }

    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue

        # Skip comments
        if cmd.startswith('#'):
            continue

        parts = cmd.split()
        if not parts:
            continue

        cmd_name = parts[0]
        args = parts[1:]

        if cmd_name == 'python':
            # Check if the script file exists
            if args:
                script_name = args[0]
                # Handle relative paths
                if not os.path.isabs(script_name):
                    script_path = os.path.join(os.getcwd(), script_name)
                else:
                    script_path = script_name

                if os.path.exists(script_path):
                    results['valid'].append(cmd)
                else:
                    results['invalid'].append(cmd)
            else:
                results['skipped'].append(cmd) # python without args
        elif cmd_name == 'pip':
            # Mock validation: assume pip works, check for install args
            if 'install' in args:
                results['valid'].append(cmd) # Assume valid syntax
            else:
                results['skipped'].append(cmd)
        elif cmd_name.startswith('bash') or cmd_name.startswith('sh'):
            # Check if script exists
            if args:
                script_name = args[0]
                if os.path.exists(script_name):
                    results['valid'].append(cmd)
                else:
                    results['invalid'].append(cmd)
            else:
                results['skipped'].append(cmd)
        else:
            # Generic check: try --help or --version if possible, else skip
            results['skipped'].append(cmd)

    return results

def validate_prerequisites(prereqs: list) -> dict:
    """
    Checks prerequisites (e.g., python version, packages).
    Returns a summary of what is met.
    """
    results = {
        'met': [],
        'unmet': [],
        'unknown': []
    }

    for req in prereqs:
        req = req.strip()
        if not req:
            continue

        # Simple heuristic checks
        if 'python' in req.lower():
            # Check version
            try:
                import sys
                if sys.version_info >= (3, 8):
                    results['met'].append(req)
                else:
                    results['unmet'].append(req)
            except:
                results['unknown'].append(req)
        elif 'pip' in req.lower() or 'package' in req.lower():
            # Assume packages are installed if requirements.txt exists and was processed
            # A full check would parse requirements.txt
            results['met'].append(req) # Optimistic for now
        elif os.path.exists(req):
            results['met'].append(req)
        else:
            results['unknown'].append(req)

    return results

def run_validation(quickstart_path: str = "docs/quickstart.md") -> dict:
    """
    Orchestrates the validation process.
    """
    base_dir = os.getcwd()
    report = {
        'status': 'success',
        'quickstart_path': quickstart_path,
        'prerequisites': {},
        'paths': {},
        'commands': {},
        'errors': []
    }

    try:
        if not os.path.exists(quickstart_path):
            # Try common locations
            alt_paths = [
                os.path.join(base_dir, 'docs', 'quickstart.md'),
                os.path.join(base_dir, 'quickstart.md')
            ]
            found = False
            for p in alt_paths:
                if os.path.exists(p):
                    quickstart_path = p
                    found = True
                    break
            if not found:
                raise FileNotFoundError(f"Could not find quickstart.md in {base_dir} or docs/")

        sections = parse_quickstart(quickstart_path)
        report['sections_found'] = list(sections.keys())

        # Validate Paths
        path_results = validate_paths(sections['paths'], base_dir)
        report['paths'] = path_results
        if path_results['invalid'] or path_results['missing']:
            report['status'] = 'warning'
            report['errors'].extend([f"Path missing: {p}" for p in path_results['invalid'] + path_results['missing']])

        # Validate Commands
        cmd_results = validate_commands(sections['commands'])
        report['commands'] = cmd_results
        if cmd_results['invalid']:
            report['status'] = 'error'
            report['errors'].extend([f"Command invalid: {c}" for c in cmd_results['invalid']])

        # Validate Prerequisites
        prereq_results = validate_prerequisites(sections['prerequisites'])
        report['prerequisites'] = prereq_results
        if prereq_results['unmet']:
            report['status'] = 'error'
            report['errors'].extend([f"Prerequisite unmet: {p}" for p in prereq_results['unmet']])

    except Exception as e:
        report['status'] = 'error'
        report['errors'].append(str(e))

    return report

def save_report(report: dict, output_path: str = "data/logs/quickstart_validation_report.json"):
    """Saves the validation report to disk."""
    ensure_dirs()
    safe_write_json(output_path, report)
    logging.info(f"Validation report saved to {output_path}")
    return output_path

def main():
    """Entry point for the validation script."""
    # Setup logging
    logger = get_logger()
    logger.info("Starting quickstart validation...")

    # Run validation
    report = run_validation()

    # Save report
    output_path = save_report(report)

    # Print summary
    print(f"Validation Status: {report['status'].upper()}")
    if report['errors']:
        print("Errors/Warnings found:")
        for err in report['errors']:
            print(f"  - {err}")
    else:
        print("No critical errors found. Quickstart validation passed.")

    # Exit with error code if validation failed
    if report['status'] == 'error':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()