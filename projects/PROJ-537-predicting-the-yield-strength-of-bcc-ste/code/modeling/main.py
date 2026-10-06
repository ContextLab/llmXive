"""
Main entry point for the modeling pipeline.
Orchestrates feature engineering, training, and evaluation.
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
from modeling.features import main as features_main
from modeling.train import main as train_main
from modeling.evaluate import main as evaluate_main
from modeling.save_results import main as save_results_main

logger = get_logger("modeling.main")

def run_pipeline():
    """Run the complete modeling pipeline."""
    logger.info("Starting modeling pipeline...")

    try:
        # Step 1: Feature engineering
        logger.info("Step 1: Engineering features...")
        features_main()

        # Step 2: Train models
        logger.info("Step 2: Training models...")
        train_main()

        # Step 3: Evaluate models
        logger.info("Step 3: Evaluating models...")
        evaluate_main()

        # Step 4: Save results
        logger.info("Step 4: Saving results...")
        save_results_main()

        logger.info("Modeling pipeline completed successfully")
        log_provenance_event("modeling_completed", {"status": "success"})

    except Exception as e:
        logger.error(f"Modeling pipeline failed: {str(e)}")
        log_provenance_event("modeling_failed", {"error": str(e)})
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
