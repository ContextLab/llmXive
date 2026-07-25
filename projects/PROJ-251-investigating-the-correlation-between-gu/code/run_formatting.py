"""
Script to run ruff and black formatting on the project code.
This script is the entry point for task T039.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(command: list, cwd: Path) -> dict:
    """
    Run a command and capture return code, stdout, stderr.
    """
    logger.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return {
            "returncode": -1,
            "stdout": "",
            "stderr": str(e)
        }

def main():
    """
    Main function to execute ruff and black formatting.
    """
    project_root = Path.cwd()
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    logger.info(f"Starting formatting check on {code_dir}")
    
    results = {
        "ruff_check": None,
        "ruff_fix": None,
        "black_format": None,
        "success": False
    }
    
    # Step 1: Run ruff check
    logger.info("Step 1: Running ruff check...")
    ruff_check_result = run_command(["ruff", "check", str(code_dir)], project_root)
    results["ruff_check"] = {
        "returncode": ruff_check_result["returncode"],
        "output": ruff_check_result["stdout"] + ruff_check_result["stderr"]
    }
    
    if ruff_check_result["returncode"] != 0:
        logger.warning("Ruff check found issues. Attempting to fix...")
        ruff_fix_result = run_command(["ruff", "check", str(code_dir), "--fix"], project_root)
        results["ruff_fix"] = {
            "returncode": ruff_fix_result["returncode"],
            "output": ruff_fix_result["stdout"] + ruff_fix_result["stderr"]
        }
        
        if ruff_fix_result["returncode"] != 0:
            logger.error("Ruff fix failed or issues remain.")
            logger.error(ruff_fix_result["stdout"])
            logger.error(ruff_fix_result["stderr"])
        else:
            logger.info("Ruff fix successful.")
    else:
        logger.info("Ruff check passed.")
    
    # Step 2: Run black format
    logger.info("Step 2: Running black format...")
    black_result = run_command(["black", str(code_dir)], project_root)
    results["black_format"] = {
        "returncode": black_result["returncode"],
        "output": black_result["stdout"] + black_result["stderr"]
    }
    
    if black_result["returncode"] == 0:
        logger.info("Black formatting successful.")
    else:
        logger.error("Black formatting failed.")
        logger.error(black_result["stderr"])
    
    # Determine overall success
    ruff_ok = (ruff_check_result["returncode"] == 0) or (
        ruff_check_result["returncode"] != 0 and 
        results.get("ruff_fix") and 
        results["ruff_fix"]["returncode"] == 0
    )
    black_ok = black_result["returncode"] == 0
    
    results["success"] = ruff_ok and black_ok
    
    # Write results to log file
    log_file = project_root / "data" / "results" / "formatting_log.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Formatting log written to {log_file}")
    
    if results["success"]:
        logger.info("All formatting and linting checks passed.")
        sys.exit(0)
    else:
        logger.error("Formatting or linting checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()