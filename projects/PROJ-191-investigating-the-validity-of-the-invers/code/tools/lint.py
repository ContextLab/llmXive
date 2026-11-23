import subprocess
import sys
from pathlib import Path
import logging
from config import get_logger

def run_command(command: list[str]) -> int:
    """
    Execute a shell command and return the exit code.
    Logs the command and its output.
    """
    logger = get_logger()
    logger.info(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=False,
            text=True
        )
        return result.returncode
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return 1

def main() -> int:
    """
    Entry point for the linting tool.
    Runs ruff check on the code directory.
    """
    logger = get_logger()
    logger.info("Starting linting process with ruff...")
    
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1
    
    # Run ruff check
    # Using --fix to automatically fix simple issues if possible
    # Using --show-source and --show-fixes for better diagnostics
    command = [
        sys.executable, "-m", "ruff", "check",
        str(code_dir),
        "--output-format", "concise"
    ]
    
    return_code = run_command(command)
    
    if return_code == 0:
        logger.info("Linting passed: No issues found.")
    else:
        logger.warning(f"Linting found {return_code} issue(s). Run 'python code/tools/format.py' to auto-fix.")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())
