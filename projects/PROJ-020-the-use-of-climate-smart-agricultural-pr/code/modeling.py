"""
Modeling entry point script.

This script orchestrates the statistical modeling pipeline:
1. Loads processed data and features.
2. Runs the Fixed-Effects Regression Model (T023).
3. Runs Collinearity Diagnostics (T024).
4. Applies Multiple Hypothesis Correction (T025).
5. Runs Robustness Checks (T026).
6. Saves all results to data/processed/.

This script is invoked by the quickstart run-book to perform the modeling phase.
"""
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.features import main as features_main
from analysis.model import main as model_main
from analysis.diagnostics import main as diagnostics_main
from analysis.robustness import main as robustness_main
from utils.config import get_processed_data_dir, get_data_dir
from utils.logging import initialize_logging

def main():
    """
    Orchestrates the full modeling pipeline.
    """
    # Initialize logging
    log_file = project_root / "data" / "state" / "modeling.log"
    initialize_logging(log_file, level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Modeling Pipeline (T045)")
    
    # 1. Ensure features are constructed (T022)
    # This step constructs the CSA Index and saves it to data/processed/features.parquet
    logger.info("Step 1: Constructing CSA Index features (T022)...")
    try:
        features_main()
        logger.info("Features construction completed.")
    except Exception as e:
        logger.error(f"Failed to construct features: {e}")
        raise

    # 2. Run the Fixed-Effects Regression Model (T023)
    # This step fits the model and saves results to data/processed/model_results.json
    logger.info("Step 2: Running Fixed-Effects Regression Model (T023)...")
    try:
        model_main()
        logger.info("Model fitting completed.")
    except Exception as e:
        logger.error(f"Failed to run model: {e}")
        raise

    # 3. Run Collinearity Diagnostics (T024)
    # This step calculates VIF and saves diagnostics to data/processed/diagnostics.json
    logger.info("Step 3: Running Collinearity Diagnostics (T024)...")
    try:
        diagnostics_main()
        logger.info("Diagnostics completed.")
    except Exception as e:
        logger.error(f"Failed to run diagnostics: {e}")
        raise

    # 4. Run Robustness Checks (T026) & Hypothesis Correction (T025)
    # The robustness script internally handles multiple hypothesis correction and saves robustness_results.json
    logger.info("Step 4: Running Robustness Checks & Hypothesis Correction (T025, T026)...")
    try:
        robustness_main()
        logger.info("Robustness checks completed.")
    except Exception as e:
        logger.error(f"Failed to run robustness checks: {e}")
        raise

    # 5. Final Summary
    logger.info("Modeling Pipeline completed successfully.")
    logger.info("Outputs generated:")
    logger.info(f"  - {get_processed_data_dir()}/features.parquet")
    logger.info(f"  - {get_processed_data_dir()}/model_results.json")
    logger.info(f"  - {get_processed_data_dir()}/diagnostics.json")
    logger.info(f"  - {get_processed_data_dir()}/robustness_results.json")

    return 0

if __name__ == "__main__":
    sys.exit(main())