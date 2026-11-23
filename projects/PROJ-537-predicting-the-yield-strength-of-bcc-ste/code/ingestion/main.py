"""
Main entry point for the ingestion pipeline.
Orchestrates fetching, merging, and validating data.
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
from ingestion.fetch_experimental import fetch_experimental_data
from ingestion.fetch_dft import fetch_dft_data
from ingestion.merge_and_filter import main as merge_and_filter_main
from ingestion.generate_checksums import main as generate_checksums_main
from ingestion.update_state import main as update_state_main

logger = get_logger("ingestion.main")

def run_pipeline():
    """Run the complete ingestion pipeline."""
    logger.info("Starting ingestion pipeline...")

    try:
        # Step 1: Fetch experimental data
        logger.info("Step 1: Fetching experimental data...")
        fetch_experimental_data()

        # Step 2: Fetch DFT data
        logger.info("Step 2: Fetching DFT data from Materials Project...")
        fetch_dft_data()

        # Step 3: Merge and filter
        logger.info("Step 3: Merging and filtering datasets...")
        merge_and_filter_main()

        # Step 4: Generate checksums
        logger.info("Step 4: Generating checksums...")
        generate_checksums_main()

        # Step 5: Update state
        logger.info("Step 5: Updating project state...")
        update_state_main()

        logger.info("Ingestion pipeline completed successfully")
        log_provenance_event("ingestion_completed", {"status": "success"})

    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        log_provenance_event("ingestion_failed", {"error": str(e)})
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
