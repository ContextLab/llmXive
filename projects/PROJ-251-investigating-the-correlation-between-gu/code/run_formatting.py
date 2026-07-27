import os
import sys
import subprocess
import json
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for the formatting run."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """
    Orchestrates the formatting process:
    1. Runs ruff check and fix
    2. Runs black format
    3. Logs results
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1
    
    logger.info(f"Starting formatting pipeline for {code_dir}")
    
    # Import formatting utilities
    sys.path.insert(0, str(project_root / "code"))
    from formatting_utils import run_ruff_check_and_fix, run_black_format
    
    # Step 1: Ruff Check and Fix
    logger.info("Step 1: Running Ruff Check and Fix...")
    ruff_success = run_ruff_check_and_fix(code_dir)
    
    # Step 2: Black Format
    logger.info("Step 2: Running Black Format...")
    black_success = run_black_format(code_dir)
    
    # Step 3: Final Verification (Ruff Check without fix)
    logger.info("Step 3: Final Ruff Verification...")
    final_check_command = [
        sys.executable, "-m", "ruff", "check",
        str(code_dir)
    ]
    result = subprocess.run(final_check_command, cwd=project_root, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("Final verification passed: No remaining ruff issues.")
    else:
        logger.warning(f"Final verification found remaining issues:\n{result.stdout}")
    
    # Summary
    if ruff_success and black_success:
        logger.info("Formatting pipeline completed successfully.")
        return 0
    else:
        logger.warning("Formatting pipeline completed with warnings.")
        return 0  # Non-fatal for pipeline

if __name__ == "__main__":
    sys.exit(main())