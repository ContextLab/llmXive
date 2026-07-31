"""
Linting utility script for the llmXive pipeline.
Runs ruff check on the codebase and writes results to a log file.
"""
import subprocess
import sys
import logging
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_ruff_check():
    """
    Runs ruff check on the code/ directory.
    Returns (success: bool, output: str, error: str)
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    output_log_path = get_path("processed", "lint_log.txt")

    logger.info(f"Running ruff check on {code_dir}...")

    try:
        # Run ruff check
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )

        output = result.stdout
        error = result.stderr
        return_code = result.returncode

        # Write output to log file
        ensure_dir(output_log_path.parent)
        with open(output_log_path, 'w', encoding='utf-8') as f:
            f.write(f"RUFF CHECK LOG\n")
            f.write(f"==============\n")
            f.write(f"Command: ruff check code/\n")
            f.write(f"Return Code: {return_code}\n")
            f.write(f"Output:\n{output}\n")
            if error:
                f.write(f"Stderr:\n{error}\n")

        if return_code != 0:
            logger.error(f"Ruff check failed with return code {return_code}")
            logger.error(f"Output:\n{output}")
            if error:
                logger.error(f"Stderr:\n{error}")
            return False, output, error
        else:
            logger.info("Ruff check passed successfully.")
            return True, output, error

    except FileNotFoundError:
        msg = "ruff is not installed. Please install it with: pip install ruff"
        logger.error(msg)
        # Write error to log file even on exception
        ensure_dir(output_log_path.parent)
        with open(output_log_path, 'w', encoding='utf-8') as f:
            f.write(f"RUFF CHECK ERROR\n")
            f.write(f"================\n")
            f.write(f"Error: {msg}\n")
        return False, "", msg
    except Exception as e:
        msg = f"Unexpected error running ruff: {str(e)}"
        logger.error(msg)
        ensure_dir(output_log_path.parent)
        with open(output_log_path, 'w', encoding='utf-8') as f:
            f.write(f"RUFF CHECK ERROR\n")
            f.write(f"================\n")
            f.write(f"Error: {str(e)}\n")
        return False, "", str(e)

def main():
    """
    Main entry point for the linting task.
    """
    success, output, error = run_ruff_check()
    if not success:
        # Exit with non-zero code to signal failure to the orchestrator
        sys.exit(1)
    else:
        print("Linting passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
