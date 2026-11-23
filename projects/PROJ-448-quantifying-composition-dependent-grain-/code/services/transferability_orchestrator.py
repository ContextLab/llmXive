import logging
import sys
from pathlib import Path

from code.config import PROCESSED_PATH, get_logger
from code.services.transferability_check import main as transferability_main

logger = get_logger(__name__)

def main():
    """
    Orchestrates the transferability check (T031).
    Ensures dependencies are met and runs the core check.
    """
    logger.info("Starting T031 Transferability Orchestrator")
    
    # Check for required input files
    interaction_terms_path = PROCESSED_PATH / "interaction_terms.csv"
    if not interaction_terms_path.exists():
        logger.error(f"Required input file missing: {interaction_terms_path}")
        logger.error("Please ensure T021a-Persist has been executed successfully.")
        sys.exit(1)
    
    logger.info(f"Input file found: {interaction_terms_path}")
    
    # Run the transferability check
    results = transferability_main()
    
    if results["status"] == "success":
        logger.info("Transferability check completed successfully.")
        logger.info(f"Train R2: {results['train_r2']:.4f}, Test R2: {results['test_r2']:.4f}")
        if results['test_r2'] < 0.5:
            logger.warning("Low test R2 indicates poor transferability between Fe-Cr-Mo and Fe-Cr-V.")
    else:
        logger.error(f"Transferability check failed: {results.get('reason')}")
        # Do not exit with error code here to allow pipeline to continue if this is optional
        # But T031 is a task, so we might want to mark it as failed in a report.
    
    return results

if __name__ == "__main__":
    main()