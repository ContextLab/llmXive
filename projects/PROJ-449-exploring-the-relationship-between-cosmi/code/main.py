"""
Main entry point for the cosmic ray composition and solar activity pipeline.
Orchestrates the full data pipeline: fetch, align, preprocess, and output.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging import setup_logger
from code.utils.config import CONFIG
from code.data.fetch_ams02 import main as fetch_ams02_main
from code.data.fetch_noaa import main as fetch_noaa_main
from code.data.align_data import main as align_data_main
from code.data.preprocess import main as preprocess_main

def main():
    """
    Orchestrates the full data pipeline:
    1. Fetch AMS-02 flux data
    2. Fetch NOAA sunspot data
    3. Align datasets by date
    4. Calculate composition ratios
    5. Output unified_timeseries.csv
    """
    # Setup logging
    logger = setup_logger("main_pipeline", level=logging.INFO)
    logger.info("Starting cosmic ray composition analysis pipeline...")

    try:
        # Step 1: Fetch AMS-02 data
        logger.info("Step 1: Fetching AMS-02 data...")
        fetch_ams02_main()
        logger.info("AMS-02 data fetch complete.")

        # Step 2: Fetch NOAA sunspot data
        logger.info("Step 2: Fetching NOAA sunspot data...")
        fetch_noaa_main()
        logger.info("NOAA sunspot data fetch complete.")

        # Step 3: Align datasets
        logger.info("Step 3: Aligning datasets...")
        align_data_main()
        logger.info("Data alignment complete.")

        # Step 4: Calculate composition ratios
        logger.info("Step 4: Calculating composition ratios...")
        preprocess_main()
        logger.info("Composition ratio calculation complete.")

        logger.info("Pipeline execution successful.")
        logger.info(f"Output available at: {CONFIG['output_file']}")
        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
