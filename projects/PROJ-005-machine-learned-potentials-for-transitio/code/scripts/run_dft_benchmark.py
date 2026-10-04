"""
Script to execute the DFT benchmark (T036b).

This script wraps the DFT benchmark executor and ensures proper logging
and error handling for the execution stage.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.analysis.dft_benchmark_executor import main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting DFT benchmark execution script")
    exit_code = main()
    logger.info(f"DFT benchmark script finished with exit code {exit_code}")
    sys.exit(exit_code)
