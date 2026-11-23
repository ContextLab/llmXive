import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/syntax_validation.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

def find_python_scripts(code_dir: Path) -> List[Path]:
    """Find all Python scripts in the code directory."""
    scripts = []
    for file_path in code_dir.rglob("*.py"):
        # Skip __pycache__ directories
        if "__pycache__" in str(file_path):
            continue
        scripts.append(file_path)
    return sorted(scripts)

def find_r_scripts(code_dir: Path) -> List[Path]:
    """Find all R scripts in the code directory."""
    scripts = []
    for file_path in code_dir.rglob("*.R"):
        scripts.append(file_path)
    return sorted(scripts)

def validate_python_syntax(script_path: Path, venv_python: str) -> Tuple[bool, str]:
    """Validate Python syntax using py_compile."""
    try:
        result = subprocess.run(
            [venv_python, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            logger.info(f"PASS: {script_path.relative_to(Path.cwd())}")
            return True, ""
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown syntax error"
            logger.error(f"FAIL: {script_path.relative_to(Path.cwd())} - {error_msg}")
            return False, error_msg
    except subprocess.TimeoutExpired:
        msg = "Timeout during validation"
        logger.error(f"FAIL: {script_path.relative_to(Path.cwd())} - {msg}")
        return False, msg
    except Exception as e:
        msg = str(e)
        logger.error(f"FAIL: {script_path.relative_to(Path.cwd())} - {msg}")
        return False, msg

def validate_r_syntax(script_path: Path) -> Tuple[bool, str]:
    """Validate R syntax using R -e 'source(...)'. """
    try:
        # Use Rscript to source the file and check for errors
        # R's source() returns an error code if there's a syntax error
        cmd = [
            "Rscript", "-e",
            f"tryCatch(source('{script_path}', local = FALSE), error = function(e) stop(e))"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            logger.info(f"PASS: {script_path.relative_to(Path.cwd())}")
            return True, ""
        else:
            error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
            if not error_msg:
                error_msg = "Unknown R syntax error"
            logger.error(f"FAIL: {script_path.relative_to(Path.cwd())} - {error_msg}")
            return False, error_msg
    except subprocess.TimeoutExpired:
        msg = "Timeout during validation"
        logger.error(f"FAIL: {script_path.relative_to(Path.cwd())} - {msg}")
        return False, msg
    except Exception as e:
        msg = str(e)
        logger.error(f"FAIL: {script_path.relative_to(Path.cwd())} - {msg}")
        return False, msg

def main():
    parser = argparse.ArgumentParser(description="Syntax validation for llmXive pipeline scripts.")
    parser.add_argument(
        "--code-dir",
        type=Path,
        default=Path("code"),
        help="Directory containing scripts to validate (default: code/)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/syntax_validation.log"),
        help="Path to output log file (default: results/syntax_validation.log)"
    )
    parser.add_argument(
        "--venv-python",
        type=str,
        default=None,
        help="Path to Python interpreter in virtual environment (auto-detect if not provided)"
    )
    args = parser.parse_args()

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Auto-detect venv Python if not provided
    venv_python = args.venv_python
    if not venv_python:
        # Check common venv locations
        possible_paths = [
            Path(".venv/bin/python"),
            Path("venv/bin/python"),
            Path(".conda/bin/python"),
        ]
        for p in possible_paths:
            if p.exists():
                venv_python = str(p)
                logger.info(f"Auto-detected venv Python: {venv_python}")
                break
        if not venv_python:
            # Fall back to system python
            venv_python = sys.executable
            logger.warning(f"Could not find venv Python, using system Python: {venv_python}")

    logger.info(f"Starting syntax validation for scripts in: {args.code_dir}")
    logger.info(f"Using Python interpreter: {venv_python}")

    # Find scripts
    python_scripts = find_python_scripts(args.code_dir)
    r_scripts = find_r_scripts(args.code_dir)

    logger.info(f"Found {len(python_scripts)} Python scripts and {len(r_scripts)} R scripts.")

    results = {
        "python": {"passed": 0, "failed": 0, "errors": []},
        "r": {"passed": 0, "failed": 0, "errors": []},
        "summary": {
            "total_python": len(python_scripts),
            "total_r": len(r_scripts),
            "total_passed": 0,
            "total_failed": 0,
            "success": True
        }
    }

    # Validate Python scripts
    logger.info("-" * 60)
    logger.info("Validating Python scripts...")
    for script in python_scripts:
        success, error = validate_python_syntax(script, venv_python)
        if success:
            results["python"]["passed"] += 1
        else:
            results["python"]["failed"] += 1
            results["python"]["errors"].append({
                "script": str(script.relative_to(Path.cwd())),
                "error": error
            })
            results["summary"]["success"] = False

    # Validate R scripts
    logger.info("-" * 60)
    logger.info("Validating R scripts...")
    for script in r_scripts:
        success, error = validate_r_syntax(script)
        if success:
            results["r"]["passed"] += 1
        else:
            results["r"]["failed"] += 1
            results["r"]["errors"].append({
                "script": str(script.relative_to(Path.cwd())),
                "error": error
            })
            results["summary"]["success"] = False

    # Update summary
    results["summary"]["total_passed"] = results["python"]["passed"] + results["r"]["passed"]
    results["summary"]["total_failed"] = results["python"]["failed"] + results["r"]["failed"]

    # Write summary to log file
    with open(args.output, 'w') as f:
        f.write(f"Syntax Validation Report\n")
        f.write(f"=" * 60 + "\n\n")
        f.write(f"Python Scripts:\n")
        f.write(f"  Total: {results['summary']['total_python']}\n")
        f.write(f"  Passed: {results['python']['passed']}\n")
        f.write(f"  Failed: {results['python']['failed']}\n")
        if results["python"]["errors"]:
            f.write(f"  Errors:\n")
            for err in results["python"]["errors"]:
                f.write(f"    - {err['script']}: {err['error']}\n")
        
        f.write(f"\nR Scripts:\n")
        f.write(f"  Total: {results['summary']['total_r']}\n")
        f.write(f"  Passed: {results['r']['passed']}\n")
        f.write(f"  Failed: {results['r']['failed']}\n")
        if results["r"]["errors"]:
            f.write(f"  Errors:\n")
            for err in results["r"]["errors"]:
                f.write(f"    - {err['script']}: {err['error']}\n")

        f.write(f"\nSummary:\n")
        f.write(f"  Total Passed: {results['summary']['total_passed']}\n")
        f.write(f"  Total Failed: {results['summary']['total_failed']}\n")
        f.write(f"  Overall Status: {'SUCCESS' if results['summary']['success'] else 'FAILURE'}\n")
        f.write(f"\n" + "=" * 60 + "\n")
        if not results["summary"]["success"]:
            f.write("VALIDATION FAILED: Please fix the syntax errors listed above.\n")
        else:
            f.write("VALIDATION SUCCESSFUL: All scripts have valid syntax.\n")

    logger.info("-" * 60)
    logger.info(f"Validation complete. Results written to: {args.output}")
    logger.info(f"Overall Status: {'SUCCESS' if results['summary']['success'] else 'FAILURE'}")

    # Exit with error code if validation failed
    if not results["summary"]["success"]:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
