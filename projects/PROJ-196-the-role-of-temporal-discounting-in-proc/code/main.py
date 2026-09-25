import argparse
import sys
import os
import json
from pathlib import Path
from typing import Dict

# Import from new modules
from data.generate_dgp import generate_synthetic_data
from data.harmonize import harmonize_datasets
from modeling import run_full_analysis
from robustness import run_robustness_checks
from utils.checksum import update_all_artifacts_in_directory

from config import get_project_root, get_config, get_random_state

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline for Temporal Discounting Study")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    parser.add_argument('--n', type=int, default=500, help="Number of participants")
    args = parser.parse_args()

    project_root = get_project_root()
    os.makedirs(project_root / 'logs', exist_ok=True)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(project_root / 'logs' / 'pipeline.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Step 1: Data Generation (T040 - generate_dgp.py)
    logger.info("Step 1: Generating Data...")
    try:
        data_dict = generate_synthetic_data(args.n, args.seed)
    except Exception as e:
        logger.error(f"Data generation failed: {e}")
        sys.exit(1)

    # Step 2: Harmonization (T040 - harmonize.py)
    logger.info("Step 2: Harmonizing Data...")
    try:
        harmonized_df = harmonize_datasets(data_dict)
    except SystemExit as e:
        if e.code != 0:
            logger.error("Harmonization failed due to validation error.")
            sys.exit(1)
        harmonized_df = None # Should not happen if no exit
    
    if harmonized_df is not None:
        # Step 3: Analysis
        logger.info("Step 3: Running Analysis...")
        run_full_analysis()
        
        # Step 4: Robustness
        logger.info("Step 4: Running Robustness Checks...")
        run_robustness_checks()
        
        logger.info("Pipeline completed successfully.")
    else:
        logger.error("Pipeline halted before analysis.")
        sys.exit(1)

if __name__ == "__main__":
    main()
