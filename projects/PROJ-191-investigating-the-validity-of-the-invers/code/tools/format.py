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
    Entry point for the formatting tool.
    Runs black on the code directory.
    """
    logger = get_logger()
    logger.info("Starting formatting process with black...")
    
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1
    
    # Run black
    command = [
        sys.executable, "-m", "black",
        str(code_dir),
        "--line-length", "88"
    ]
    
    return_code = run_command(command)
    
    if return_code == 0:
        logger.info("Formatting complete: All files formatted successfully.")
    else:
        logger.warning(f"Formatting encountered issues. Exit code: {return_code}")
    
    return return_code

if __name__ == "__main__":
    sys.exit(main())
