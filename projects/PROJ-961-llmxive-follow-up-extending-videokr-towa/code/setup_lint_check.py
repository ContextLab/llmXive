"""
Lint check script for the llmXive project.
Runs ruff check on the code/ directory and logs the output.
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

def run_ruff_check() -> bool:
    """
    Run ruff check on the code/ directory.
    
    Returns:
        bool: True if ruff check passes (exit code 0), False otherwise.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    processed_dir = project_root / "data" / "processed"
    
    # Ensure the processed directory exists
    ensure_dir(processed_dir)
    
    # Path to the log file
    log_file = processed_dir / "lint_log.txt"
    
    logger.info(f"Running ruff check on {code_dir}...")
    
    try:
        # Run ruff check
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        # Write output to log file
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Command: ruff check {code_dir}\n")
            f.write(f"Exit code: {result.returncode}\n")
            f.write("-" * 80 + "\n")
            if result.stdout:
                f.write("STDOUT:\n")
                f.write(result.stdout)
            if result.stderr:
                f.write("\nSTDERR:\n")
                f.write(result.stderr)
            if not result.stdout and not result.stderr:
                f.write("No output from ruff.\n")
        
        logger.info(f"Ruff check output written to {log_file}")
        
        if result.returncode != 0:
            logger.error(f"Ruff check failed with exit code {result.returncode}")
            logger.error(f"See {log_file} for details")
            return False
        
        logger.info("Ruff check passed successfully")
        return True
        
    except FileNotFoundError:
        error_msg = "ruff not found. Please install it with: pip install ruff"
        logger.error(error_msg)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Error: {error_msg}\n")
            f.write("Please install ruff and try again.\n")
        return False
    except Exception as e:
        error_msg = f"Unexpected error running ruff check: {str(e)}"
        logger.error(error_msg)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"Error: {error_msg}\n")
        return False

def main():
    """Main entry point for the lint check script."""
    logger.info("Starting lint check...")
    success = run_ruff_check()
    
    if success:
        logger.info("Lint check completed successfully")
        sys.exit(0)
    else:
        logger.error("Lint check failed")
        sys.exit(1)

if __name__ == "__main__":
    main()