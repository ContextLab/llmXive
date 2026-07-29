import subprocess
import sys
import os
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any

from utils.config import get_project_root, get_path, ensure_dir

def run_mypy_check() -> int:
    """
    Run mypy type checking on the code/ directory.

    Returns:
        int: 0 if type checking passes (exit code 0), 1 otherwise.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    processed_dir = project_root / "data" / "processed"
    ensure_dir(processed_dir)
    log_path = processed_dir / "type_log.txt"

    logging.info("Running mypy type check on code/ directory...")

    try:
        # Run mypy on the code directory
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--ignore-missing-imports", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300
        )

        # Write output to log file
        with open(log_path, "w") as f:
            f.write("STDOUT:\n")
            f.write(result.stdout)
            f.write("\nSTDERR:\n")
            f.write(result.stderr)
            f.write(f"\nReturn Code: {result.returncode}\n")

        if result.returncode == 0:
            logging.info("Type check passed successfully.")
            return 0
        else:
            logging.error("Type check failed. See data/processed/type_log.txt for details.")
            return 1

    except subprocess.TimeoutExpired:
        logging.error("mypy check timed out.")
        with open(log_path, "w") as f:
            f.write("Error: mypy check timed out after 300 seconds.\n")
        return 1
    except FileNotFoundError:
        logging.error("mypy not found. Please install it: pip install mypy")
        with open(log_path, "w") as f:
            f.write("Error: mypy not found. Please install it: pip install mypy\n")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error during type check: {e}")
        with open(log_path, "w") as f:
            f.write(f"Error: {str(e)}\n")
        return 1

def main() -> None:
    """
    Main entry point for the type check script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    exit_code = run_mypy_check()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()