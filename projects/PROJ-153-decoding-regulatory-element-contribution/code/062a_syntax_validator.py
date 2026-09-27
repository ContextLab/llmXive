"""
Syntax Validation Script for llmXive Pipeline (Task T62a).

This script performs a comprehensive syntax check on all Python and R scripts
in the project to ensure zero syntax errors before final handoff.

It outputs:
1. A JSON report to `results/syntax_validation_report.json`
2. A summary log to `results/syntax_validation_summary.txt`

It exits with code 0 if all checks pass, and code 1 if any errors are found.
"""
import os
import sys
import subprocess
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/syntax_validation.log')
    ]
)
logger = logging.getLogger(__name__)

def find_python_scripts(code_dir: Path) -> List[Path]:
    """Recursively find all .py files in the code directory."""
    scripts = []
    for root, _, files in os.walk(code_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                scripts.append(Path(root) / file)
    return sorted(scripts)

def find_r_scripts(code_dir: Path) -> List[Path]:
    """Recursively find all .R and .r files in the code directory."""
    scripts = []
    for root, _, files in os.walk(code_dir):
        for file in files:
            if file.endswith(('.R', '.r')) and not file.startswith('.'):
                scripts.append(Path(root) / file)
    return sorted(scripts)

def validate_python_syntax(script_path: Path) -> Tuple[bool, str]:
    """
    Validate Python syntax using py_compile.
    Returns (success, error_message).
    """
    try:
        # Use subprocess to run py_compile to capture stderr correctly
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, ""
        else:
            # py_compile outputs to stderr
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = "Syntax error detected but no details provided."
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Timeout during compilation"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_r_syntax(script_path: Path) -> Tuple[bool, str]:
    """
    Validate R syntax using R -e "source(...)".
    Returns (success, error_message).
    """
    try:
        # We use Rscript -e to avoid interactive prompts
        # We wrap in tryCatch to ensure R exits with 0 even if source fails,
        # so we can parse the output ourselves.
        cmd = [
            'Rscript', '-e',
            f'if (!suppressWarnings(source("{script_path}", local = new.env()))) {{"quit(status=1)}} else {{"quit(status=0)}}"'
        ]
        # Note: The above R command logic might be tricky with quotes.
        # A safer approach for syntax check without execution side effects is:
        # R -e "parse(file='...')"
        
        cmd_safe = [
            'Rscript', '-e',
            f'parse(file="{script_path}")'
        ]
        
        result = subprocess.run(
            cmd_safe,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, ""
        else:
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = "Syntax error detected in R script."
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Timeout during R syntax check"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Validate syntax of all Python and R scripts.")
    parser.add_argument('--code-dir', type=str, default='code', help='Directory containing code scripts.')
    parser.add_argument('--output-dir', type=str, default='results', help='Directory for output reports.')
    args = parser.parse_args()

    code_dir = Path(args.code_dir)
    output_dir = Path(args.output_dir)
    
    if not code_dir.exists():
        logger.error(f"Code directory '{code_dir}' does not exist.")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)

    python_scripts = find_python_scripts(code_dir)
    r_scripts = find_r_scripts(code_dir)

    logger.info(f"Found {len(python_scripts)} Python scripts and {len(r_scripts)} R scripts.")

    report = {
        "python_results": [],
        "r_results": [],
        "summary": {
            "total_python": len(python_scripts),
            "passed_python": 0,
            "failed_python": 0,
            "total_r": len(r_scripts),
            "passed_r": 0,
            "failed_r": 0,
            "total_passed": 0,
            "total_failed": 0
        }
    }

    all_passed = True

    # Validate Python
    logger.info("Validating Python scripts...")
    for script in python_scripts:
        success, error = validate_python_syntax(script)
        status = "PASS" if success else "FAIL"
        logger.info(f"  [{status}] {script}")
        
        report["python_results"].append({
            "path": str(script),
            "status": status,
            "error": error if not success else None
        })
        
        if success:
            report["summary"]["passed_python"] += 1
        else:
            report["summary"]["failed_python"] += 1
            all_passed = False

    # Validate R
    logger.info("Validating R scripts...")
    for script in r_scripts:
        success, error = validate_r_syntax(script)
        status = "PASS" if success else "FAIL"
        logger.info(f"  [{status}] {script}")
        
        report["r_results"].append({
            "path": str(script),
            "status": status,
            "error": error if not success else None
        })
        
        if success:
            report["summary"]["passed_r"] += 1
        else:
            report["summary"]["failed_r"] += 1
            all_passed = False

    # Calculate totals
    report["summary"]["total_passed"] = report["summary"]["passed_python"] + report["summary"]["passed_r"]
    report["summary"]["total_failed"] = report["summary"]["failed_python"] + report["summary"]["failed_r"]

    # Write JSON Report
    json_path = output_dir / "syntax_validation_report.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"JSON report written to {json_path}")

    # Write Summary Text
    summary_path = output_dir / "syntax_validation_summary.txt"
    with open(summary_path, 'w') as f:
        f.write("SYNTAX VALIDATION SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Python Scripts: {report['summary']['passed_python']}/{report['summary']['total_python']} passed\n")
        f.write(f"R Scripts:      {report['summary']['passed_r']}/{report['summary']['total_r']} passed\n")
        f.write(f"Total:          {report['summary']['total_passed']}/{report['summary']['total_passed'] + report['summary']['total_failed']} passed\n\n")
        
        if not all_passed:
            f.write("FAILED SCRIPTS:\n")
            f.write("-" * 20 + "\n")
            for item in report["python_results"] + report["r_results"]:
                if item["status"] == "FAIL":
                    f.write(f"File: {item['path']}\n")
                    f.write(f"Error: {item['error']}\n\n")
            f.write("\nVALIDATION FAILED.\n")
        else:
            f.write("VALIDATION PASSED: All scripts have valid syntax.\n")
    
    logger.info(f"Summary written to {summary_path}")

    if not all_passed:
        logger.error("Syntax validation failed for one or more scripts.")
        sys.exit(1)
    else:
        logger.info("Syntax validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()