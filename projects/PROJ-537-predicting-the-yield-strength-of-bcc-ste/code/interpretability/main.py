"""
Main entry point for the interpretability pipeline.
Orchestrates SHAP analysis, bootstrap stability, and result finalization.
"""
import sys
import logging
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from config import CONFIG
from utils.logging import get_logger, log_provenance_event
from interpretability.shap_analysis import main as shap_main
from interpretability.bootstrap_stability import main as bootstrap_main
from interpretability.check_stability import main as check_stability_main
from interpretability.plot_results import main as plot_main
from interpretability.finalize_output import main as finalize_main

logger = get_logger("interpretability.main")

def run_pipeline():
    """Run the complete interpretability pipeline."""
    logger.info("Starting interpretability pipeline...")

    try:
        # Step 1: SHAP analysis
        logger.info("Step 1: Running SHAP analysis...")
        shap_main()

        # Step 2: Bootstrap stability analysis
        logger.info("Step 2: Running bootstrap stability analysis...")
        bootstrap_main()

        # Step 3: Check stability
        logger.info("Step 3: Checking stability criteria...")
        check_stability_main()

        # Step 4: Generate plots
        logger.info("Step 4: Generating plots...")
        plot_main()

        # Step 5: Finalize output
        logger.info("Step 5: Finalizing output...")
        finalize_main()

        logger.info("Interpretability pipeline completed successfully")
        log_provenance_event("interpretability_completed", {"status": "success"})

    except Exception as e:
        logger.error(f"Interpretability pipeline failed: {str(e)}")
        log_provenance_event("interpretability_failed", {"error": str(e)})
        raise

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(CONFIG.LOG_FILE)
        ]
    )

    run_pipeline()

if __name__ == "__main__":
    main()