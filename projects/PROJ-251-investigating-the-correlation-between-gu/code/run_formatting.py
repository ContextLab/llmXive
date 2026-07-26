"""
Script to run formatting checks and fixes on the codebase.
"""
import os
import sys
import subprocess
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.formatting_utils import run_command

def setup_logging():
    """Configure logging for the formatting script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point for running formatting checks."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting formatting checks...")
    
    # Import formatting utilities
    from code.formatting_utils import run_ruff_check_and_fix, run_black_format
    
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    # Run Ruff
    logger.info("Running Ruff check and fix...")
    ruff_success, ruff_msg = run_ruff_check_and_fix(code_dir)
    logger.info(ruff_msg)
    
    # Run Black
    logger.info("Running Black format...")
    black_success, black_msg = run_black_format(code_dir)
    logger.info(black_msg)
    
    # Generate report
    report = {
        "ruff_passed": ruff_success,
        "black_passed": black_success,
        "ruff_message": ruff_msg,
        "black_message": black_msg
    }
    
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = results_dir / "formatting_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Formatting report saved to {report_path}")
    
    if ruff_success and black_success:
        logger.info("All formatting checks passed!")
        sys.exit(0)
    else:
        logger.warning("Some formatting issues remain.")
        sys.exit(1)

if __name__ == "__main__":
    main()