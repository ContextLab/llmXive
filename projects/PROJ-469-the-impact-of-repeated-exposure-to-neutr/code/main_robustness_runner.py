"""
Runner script for Robustness Pipeline (US2)

Executes:
1. Bootstrap Analysis (T021)
2. Alpha Sweep (T022)
3. Covariate Adjustment (T023)
4. Binary Model (T024b)
5. Aggregation of all metrics (T026)
"""

import sys
from pathlib import Path
from logging_config import setup_logging, get_logger
from robustness import run_all_robustness_checks
from binary_model import run_binary_model_pipeline
from aggregate_robustness import run_aggregation_pipeline

def main():
    logger = setup_logging()
    logger.info("Starting Robustness Pipeline Runner...")

    try:
        # 1. Run all robustness checks (Bootstrap, Alpha, Covariates)
        logger.info("Step 1: Running robustness checks...")
        robustness_results = run_all_robustness_checks()
        logger.info(f"Robustness checks complete. Results saved.")

        # 2. Run Binary Model
        logger.info("Step 2: Running Binary Model...")
        binary_results = run_binary_model_pipeline()
        logger.info(f"Binary model complete. Results saved.")

        # 3. Aggregate all metrics (T026)
        logger.info("Step 3: Aggregating robustness metrics (T026)...")
        aggregated_results = run_aggregation_pipeline()
        logger.info(f"Aggregation complete.")

        logger.info("Robustness Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Robustness Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())