"""
Main entry point for the llmXive statistical sensitivity pipeline.

Orchestrates the full workflow:
1. Setup: Ensure directory structure exists.
2. US1: Generate synthetic datasets (Data Generation).
3. US2: Execute Monte Carlo simulations (Simulation Engine).
4. US3: Analyze results, compute CIs, and export visualizations/reports.
"""

import os
import sys
import logging
import argparse
from typing import Optional

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_run.log')
    ]
)
logger = logging.getLogger(__name__)

# Import pipeline stages
from setup_directories import main as setup_directories_main
from run_data_gen import main as run_data_gen_main
from run_simulation import main as run_simulation_main
from run_analyzer import main as run_analyzer_main
from export_results import main as export_results_main


def run_pipeline(args: Optional[argparse.Namespace] = None) -> int:
    """
    Execute the full statistical sensitivity analysis pipeline.

    Args:
        args: Optional parsed arguments. If None, defaults are used.

    Returns:
        0 on success, 1 for validation failure, 2 for missing inputs.
    """
    logger.info("Starting llmXive Statistical Sensitivity Pipeline")

    try:
        # Step 1: Setup Directory Structure
        logger.info("Phase 1: Ensuring directory structure...")
        setup_directories_main()

        # Step 2: Generate Synthetic Datasets (US1)
        logger.info("Phase 2: Generating synthetic datasets (US1)...")
        # Note: run_data_gen_main handles generation and saves to data/raw/
        run_data_gen_main()

        # Step 3: Execute Monte Carlo Simulations (US2)
        logger.info("Phase 3: Running Monte Carlo simulations (US2)...")
        # Note: run_simulation_main reads from data/raw/ and writes to data/processed/
        run_simulation_main()

        # Step 4: Analyze Results (US3 - Aggregation & Regression)
        logger.info("Phase 4: Analyzing simulation results (US3)...")
        # Note: run_analyzer_main aggregates data and computes statistics
        run_analyzer_main()

        # Step 5: Export Final Results and Plots (US3 - Export)
        logger.info("Phase 5: Exporting final results and plots (US3)...")
        # Note: export_results_main generates CSVs and figures
        export_results_main()

        logger.info("Pipeline completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Pipeline failed: Missing input files or directories. {e}", exc_info=True)
        return 2
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1


def main():
    """Entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Run the full statistical sensitivity analysis pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Configuration string for specific scenario (e.g., 'n=50,dist=normal')."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
        help="Output directory for results."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging."
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full pipeline (default behavior)."
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # If specific config is provided, we could theoretically narrow the run,
    # but for this implementation, we run the full pipeline as the orchestrator.
    # The underlying scripts can be modified to accept these args if needed.
    
    exit_code = run_pipeline(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()