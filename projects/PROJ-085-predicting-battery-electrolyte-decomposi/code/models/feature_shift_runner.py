"""
Runner script for T024: Feature Shift Analysis.
This script is designed to be executed after T026 (model training and saving)
to identify descriptors that enter the top 3 in high-potential (4V) but are absent
in low-potential (0-2V).
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config import get_project_root, get_validation_dir
from utils.logging_config import get_logger, save_log_summary
from models.feature_shift_analyzer import run_feature_shift_pipeline

logger = get_logger(__name__)

def main():
    logger.info("Starting T024: Feature Shift Analysis Pipeline")
    logger.info("Deviation Note: Spec's 3-5V range mapped to 4V data point.")

    try:
        result = run_feature_shift_pipeline()
        logger.info("T024 completed successfully.")
        logger.info(f"Output saved to: {result['output_file']}")
        
        # Log summary
        save_log_summary()
        return 0

    except Exception as e:
        logger.error(f"T024 failed with error: {e}", exc_info=True)
        save_log_summary()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)