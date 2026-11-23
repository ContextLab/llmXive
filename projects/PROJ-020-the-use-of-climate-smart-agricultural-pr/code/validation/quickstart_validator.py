import sys
import os
import time
import json
import logging
from pathlib import Path

from utils.config import get_processed_data_dir, get_state_dir

logger = logging.getLogger(__name__)

class QuickstartValidator:
    def __init__(self):
        self.required_files = [
            get_processed_data_dir() / "merged_sample.parquet",
            get_state_dir() / "model_results.json",
            get_state_dir() / "robustness_summary.json",
            get_processed_data_dir() / "figures" / "scatter_csa_vs_food_security.png"
        ]

    def validate(self) -> bool:
        all_exist = True
        for f in self.required_files:
            if not f.exists():
                logger.error(f"Missing required file: {f}")
                all_exist = False
            else:
                logger.info(f"Found: {f}")
        return all_exist

def main():
    validator = QuickstartValidator()
    if validator.validate():
        logger.info("Validation PASSED.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
