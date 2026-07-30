import subprocess
import sys
import os
from pathlib import Path
import logging
from typing import List, Optional, Dict, Any
from utils.config import get_project_root, get_path, ensure_dir

def run_mypy_check() -> bool:
    """
    Run mypy type checking on the code/ directory.

    Returns:
        bool: True if mypy passes (exit code 0), False otherwise.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    log_path = project_root / "data" / "processed" / "type_log.txt"

    # Ensure log directory exists
    ensure_dir(log_path.parent)

    logging.info(f"Running mypy on {code_dir}...")

    try:
        # Run mypy on the code directory
        result = subprocess.run(
            ["mypy", str(code_dir), "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        # Write output to log file
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
            f.write(result.stderr)

        logging.info(f"Type check log written to {log_path}")

        if result.returncode == 0:
            logging.info("Type checking passed successfully.")
            return True
        else:
            logging.error(f"Type checking failed with exit code {result.returncode}")
            logging.error(result.stdout)
            logging.error(result.stderr)
            return False

    except FileNotFoundError:
        logging.error("mypy not found. Please install it via 'pip install mypy'.")
        return False
    except Exception as e:
        logging.error(f"Error running mypy: {e}")
        return False

def main() -> int:
    """
    Main entry point for the type check script.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    success = run_mypy_check()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())