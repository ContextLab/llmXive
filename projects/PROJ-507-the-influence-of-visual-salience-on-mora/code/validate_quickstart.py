"""
Quickstart Validation Script.

This script validates the `quickstart.md` documentation by:
1. Parsing the document to extract executable steps (shell commands, python scripts).
2. Verifying that referenced files exist in the project structure.
3. Attempting to run non-destructive checks (e.g., --help flags, import checks).
4. Generating a validation report to `data/validation/quickstart_report.json`.

This fulfills task T041: Run quickstart.md validation.
"""
import os
import sys
import json
import subprocess
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"
REPORT_DIR = PROJECT_ROOT / "data" / "validation"
REPORT_PATH = REPORT_DIR / "quickstart_report.json"

# Files that must exist based on completed tasks
REQUIRED_FILES = [
    "code/config.py",
    "code/data_prep.py",
    "code/analysis.py",
    "code/survey_deploy.py",
    "code/data_cleaning.py",
    "code/validation.py",
    "code/human_coding.py",
    "code/manipulation_check.py",
    "data/raw/selected_ids.json", # Expected from T053
    "data/processed/stimuli_raw.csv", # Expected from T013
    "data/analysis/results.json", # Expected from T037
]

class QuickstartValidationError(Exception):
    """Raised when quickstart validation fails."""
    pass

def parse_quickstart_commands(content: str) -> List[Dict[str, Any]]:
    """
    Parses the quickstart.md content to extract shell commands and python scripts.
    Returns a list of dicts: {'type': 'shell'|'python', 'command': str, 'line_num': int}
    """
    commands = []
    lines = content.split('\n')
    in_code_block = False
    current_language = None
    current_buffer = []

    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                current_language = line.strip().replace("```", "").strip()
                current_buffer = []
            else:
                in_code_block = False
                # Process the buffer
                full_content = '\n'.join(current_buffer).strip()
                if full_content:
                    commands.append({
                        'type': 'shell' if current_language in ['bash', 'sh', 'shell'] else 'python' if current_language == 'python' else 'unknown',
                        'content': full_content,
                        'line_start': i - len(current_buffer)
                    })
                current_language = None
                current_buffer = []
        elif in_code_block:
            current_buffer.append(line)

    return commands

def verify_file_exists(path_str: str) -> bool:
    """Checks if a file exists relative to project root."""
    full_path = PROJECT_ROOT / path_str
    return full_path.exists()

def verify_dependencies_installed() -> Dict[str, bool]:
    """Checks if key dependencies can be imported."""
    deps = ['numpy', 'pandas', 'scipy', 'statsmodels', 'torch', 'transformers', 'ordinal', 'requests', 'PIL']
    results = {}
    for dep in deps:
        try:
            __import__(dep)
            results[dep] = True
        except ImportError:
            results[dep] = False
    return results

def run_validation_checks(commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes validation checks based on parsed commands.
    Returns a list of check results.
    """
    results = []

    # 1. Check for referenced files
    logger.info("Checking required files...")
    for req_file in REQUIRED_FILES:
        exists = verify_file_exists(req_file)
        results.append({
            'check': f'file_exists:{req_file}',
            'status': 'pass' if exists else 'fail',
            'details': f"Found at {PROJECT_ROOT / req_file}" if exists else "File not found"
        })
        if not exists:
            logger.warning(f"Missing required file: {req_file}")

    # 2. Check dependencies
    logger.info("Checking dependencies...")
    dep_results = verify_dependencies_installed()
    for dep, installed in dep_results.items():
        results.append({
            'check': f'dependency:{dep}',
            'status': 'pass' if installed else 'fail',
            'details': f"{dep} installed" if installed else f"{dep} missing"
        })

    # 3. Attempt to run --help or import checks for scripts mentioned in quickstart
    logger.info("Verifying script executability (dry-run)...")
    for cmd in commands:
        if cmd['type'] == 'shell':
            content = cmd['content']
            # Look for python scripts being called with --help or just existence check
            # Simple heuristic: if it looks like `python code/something.py --help`
            if 'python' in content and '--help' in content:
                # Extract script path
                parts = content.split()
                script_path = None
                for p in parts:
                    if p.startswith('code/') and p.endswith('.py'):
                        script_path = p
                        break
                
                if script_path:
                    full_script = PROJECT_ROOT / script_path
                    if full_script.exists():
                        try:
                            # Try to import to check syntax, avoiding full execution
                            # We use subprocess with --help if possible, else just import check
                            if '--help' in content:
                                result = subprocess.run(
                                    ['python', str(full_script), '--help'],
                                    capture_output=True,
                                    text=True,
                                    timeout=10,
                                    cwd=str(PROJECT_ROOT)
                                )
                                status = 'pass' if result.returncode == 0 else 'fail'
                                results.append({
                                    'check': f'script_help:{script_path}',
                                    'status': status,
                                    'details': result.stderr if result.returncode != 0 else "Help displayed successfully"
                                })
                            else:
                                # Fallback: try to compile/import
                                import importlib.util
                                spec = importlib.util.spec_from_file_location("module", full_script)
                                if spec and spec.loader:
                                    module = importlib.util.module_from_spec(spec)
                                    try:
                                        spec.loader.exec_module(module)
                                        results.append({
                                            'check': f'script_syntax:{script_path}',
                                            'status': 'pass',
                                            'details': "Syntax valid"
                                        })
                                    except Exception as e:
                                        results.append({
                                            'check': f'script_syntax:{script_path}',
                                            'status': 'fail',
                                            'details': str(e)
                                        })
                        except subprocess.TimeoutExpired:
                            results.append({
                                'check': f'script_help:{script_path}',
                                'status': 'fail',
                                'details': "Command timed out"
                            })
                        except Exception as e:
                            results.append({
                                'check': f'script_help:{script_path}',
                                'status': 'fail',
                                'details': str(e)
                            })
                    else:
                        results.append({
                            'check': f'script_exists:{script_path}',
                            'status': 'fail',
                            'details': "Script not found"
                        })

    return results

def main():
    """Main entry point for validation."""
    logger.info("Starting Quickstart Validation (T041)...")
    
    # Ensure report directory exists
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not QUICKSTART_PATH.exists():
        logger.error(f"quickstart.md not found at {QUICKSTART_PATH}")
        # Create a report indicating failure to find the file
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "failed",
            "reason": f"quickstart.md not found at {QUICKSTART_PATH}",
            "checks": []
        }
        with open(REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    # Read quickstart
    with open(QUICKSTART_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse commands
    commands = parse_quickstart_commands(content)
    logger.info(f"Found {len(commands)} code blocks in quickstart.md")

    # Run checks
    check_results = run_validation_checks(commands)

    # Determine overall status
    failures = [r for r in check_results if r['status'] == 'fail']
    overall_status = "pass" if len(failures) == 0 else "fail"

    # Build report
    report = {
        "timestamp": datetime.now().isoformat(),
        "quickstart_file": str(QUICKSTART_PATH),
        "status": overall_status,
        "total_checks": len(check_results),
        "passed": len(check_results) - len(failures),
        "failed": len(failures),
        "checks": check_results
    }

    # Save report
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation complete. Status: {overall_status}. Report saved to {REPORT_PATH}")

    if overall_status == "fail":
        logger.error(f"Validation failed with {len(failures)} errors:")
        for f in failures:
            logger.error(f"  - {f['check']}: {f['details']}")
        sys.exit(1)
    else:
        logger.info("All checks passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
