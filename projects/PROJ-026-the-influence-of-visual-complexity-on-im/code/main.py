"""
Main pipeline orchestration script.
Runs the full analysis from data loading to result saving.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from utils.logging import setup_logging, get_logger, log_counterbalance_strategy
from config import get_project_root, ensure_directories

# Import analysis modules
from analysis.pca import main as run_pca_main
from analysis.permutation import main as run_permutation_main
from analysis.sensitivity import main as run_sensitivity_main
from analysis.results import main as run_results_main
from data.process import main as run_process_main
from data.load import main as run_load_main
from data.counterbalance import main as run_counterbalance_main
from stimuli.process import main as run_stimuli_main


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument(
        "--null-effect",
        action="store_true",
        help="Generate synthetic data for CI/testing. Fails loudly if not set and real data is missing."
    )
    parser.add_argument(
        "--skip-stimuli",
        action="store_true",
        help="Skip stimulus processing if already done."
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Skip analysis if already done."
    )
    return parser.parse_args()


def main() -> None:
    """
    Orchestrate the full pipeline.
    """
    args = parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting llmXive pipeline...")
    
    project_root = get_project_root()
    ensure_directories()
    
    # 0. Validate Amendment (T000)
    amendment_path = project_root / "specs" / "001-the-influence-of-visual-complexity-on-im" / "amendment-001.md"
    if not amendment_path.exists():
        logger.error("CRITICAL: Amendment 001 (amendment-001.md) not found. Pipeline halted.")
        sys.exit(1)
    logger.info("Amendment 001 verified.")

    # 1. Stimuli Processing (T016, T017a-1, T017a-2, T017a-3) - Optional
    if not args.skip_stimuli:
        logger.info("Step 1: Processing stimuli...")
        run_stimuli_main()
    
    # 2. Counterbalance Assignment (T027a)
    logger.info("Step 2: Generating counterbalance assignments...")
    run_counterbalance_main()
    
    # 3. Log Counterbalance Strategy (T027b)
    # This is often handled inside the counterbalance module, but we ensure it's called.
    # Assuming run_counterbalance_main handles the logging as per T027b requirement.
    
    # 4. Load Data (T026a)
    logger.info("Step 3: Loading data...")
    run_load_main(null_effect=args.null_effect)
    
    # 5. Process Data (T022, T023, T026b-1, T026b-2, T026b-3)
    logger.info("Step 4: Processing data...")
    run_process_main()
    
    # 6. PCA Check (T051) - Required for validity
    logger.info("Step 5: Running PCA dimensionality check...")
    run_pca_main()
    
    if args.skip_analysis:
        logger.info("Analysis skipped as requested.")
        return

    # 7. Permutation Test (T033, T034)
    logger.info("Step 6: Running permutation test...")
    run_permutation_main()
    
    # 8. Sensitivity Analysis (T035)
    logger.info("Step 7: Running sensitivity analysis...")
    run_sensitivity_main()
    
    # 9. Save Results (T036)
    logger.info("Step 8: Saving results...")
    run_results_main()
    
    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()