"""
Validation script for the final report generation.
Ensures the report renders as Markdown within 30s on CI.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.reporting import generate_final_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30

def main():
    """
    Runs the report generation and validates it completes within the time limit.
    """
    logger.info(f"Starting report validation (Timeout: {TIMEOUT_SECONDS}s)...")
    
    output_path = project_root / "artifacts" / "final_report.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    
    try:
        # Call the main generation function from reporting.py
        # This function is expected to orchestrate loading data, models, and writing the file.
        generate_final_report(str(output_path))
        
        elapsed = time.time() - start_time
        
        if elapsed > TIMEOUT_SECONDS:
            logger.error(f"Report generation took {elapsed:.2f}s, exceeding limit of {TIMEOUT_SECONDS}s.")
            return 1

        if not output_path.exists():
            logger.error(f"Report file not found at {output_path}")
            return 1

        file_size = output_path.stat().st_size
        if file_size == 0:
            logger.error(f"Report file is empty.")
            return 1

        logger.info(f"SUCCESS: Report generated in {elapsed:.2f}s.")
        logger.info(f"Output: {output_path} ({file_size} bytes)")
        return 0

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Report generation failed after {elapsed:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())