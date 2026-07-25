"""
Script to run linting (ruff) and formatting (black) on the codebase.
This script checks and fixes code style issues.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    """Main entry point for run_formatting script."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    root = Path(__file__).resolve().parent.parent
    code_dir = root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    logger.info("Starting linting and formatting checks...")
    
    # Run ruff check
    logger.info("Running ruff check...")
    returncode, stdout, stderr = run_command(
        f"{sys.executable} -m ruff check {code_dir}"
    )
    
    if returncode == 0:
        logger.info("✓ Ruff check passed")
    else:
        logger.warning("Ruff check found issues:")
        if stdout:
            logger.warning(stdout)
        if stderr:
            logger.warning(stderr)
        
        # Try to fix automatically
        logger.info("Attempting to fix ruff issues automatically...")
        fix_returncode, fix_stdout, fix_stderr = run_command(
            f"{sys.executable} -m ruff check {code_dir} --fix"
        )
        
        if fix_returncode == 0:
            logger.info("✓ Ruff issues fixed automatically")
        else:
            logger.warning("Some ruff issues could not be fixed automatically:")
            if fix_stdout:
                logger.warning(fix_stdout)
            if fix_stderr:
                logger.warning(fix_stderr)
    
    # Run black format
    logger.info("Running black format...")
    returncode, stdout, stderr = run_command(
        f"{sys.executable} -m black --check {code_dir}"
    )
    
    if returncode == 0:
        logger.info("✓ Black format check passed")
    else:
        logger.warning("Black format issues found:")
        if stdout:
            logger.warning(stdout)
        if stderr:
            logger.warning(stderr)
        
        # Apply formatting
        logger.info("Applying black formatting...")
        format_returncode, format_stdout, format_stderr = run_command(
            f"{sys.executable} -m black {code_dir}"
        )
        
        if format_returncode == 0:
            logger.info("✓ Black formatting applied")
        else:
            logger.error("Failed to apply black formatting:")
            if format_stdout:
                logger.error(format_stdout)
            if format_stderr:
                logger.error(format_stderr)
    
    # Run ruff format (if available)
    logger.info("Running ruff format check...")
    returncode, stdout, stderr = run_command(
        f"{sys.executable} -m ruff format --check {code_dir}"
    )
    
    if returncode == 0:
        logger.info("✓ Ruff format check passed")
    else:
        logger.warning("Ruff format issues found:")
        if stdout:
            logger.warning(stdout)
        if stderr:
            logger.warning(stderr)
        
        # Apply ruff format
        logger.info("Applying ruff formatting...")
        format_returncode, format_stdout, format_stderr = run_command(
            f"{sys.executable} -m ruff format {code_dir}"
        )
        
        if format_returncode == 0:
            logger.info("✓ Ruff formatting applied")
        else:
            logger.error("Failed to apply ruff formatting:")
            if format_stdout:
                logger.error(format_stdout)
            if format_stderr:
                logger.error(format_stderr)
    
    # Create a summary report
    report_path = root / "data" / "results" / "formatting_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "timestamp": str(Path(__file__).resolve().parent),
        "ruff_check": "passed" if returncode == 0 else "issues_found",
        "black_format": "passed" if returncode == 0 else "issues_fixed",
        "ruff_format": "passed" if returncode == 0 else "issues_fixed"
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Formatting report saved to: {report_path}")
    logger.info("Linting and formatting complete.")

if __name__ == "__main__":
    main()