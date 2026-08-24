"""
Main orchestration script for the Solar Flare - Geomagnetic Storm Correlation Pipeline.

This script executes the full pipeline as defined in the run-book (quickstart.md).
It coordinates data ingestion, alignment, filtering, analysis, and validation.

Execution Order:
1. Ingest raw data (NOAA SWPC, CDAWeb)
2. Align events (Solar Flares, CMEs, Geomagnetic Storms)
3. Validate aligned events
4. Log data quality
5. Filter for analysis subset (remove recurrent storms)
6. Run statistical analysis
7. Validate metrics
8. Profile pipeline performance
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import pipeline modules
from ingest import main as ingest_main
from align import main as align_main
from validate import main as validate_main
from log_data_quality import main as log_quality_main
from filter_analysis_subset import main as filter_main
from analysis import main as analysis_main
from profiler import main as profile_main
from versioning import main as versioning_main

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "pipeline_run.log")
    ]
)
logger = logging.getLogger("Pipeline")


def run_pipeline():
    """Execute the full pipeline steps."""
    logger.info("Starting Solar Flare - Geomagnetic Storm Correlation Pipeline")
    start_time = datetime.now()

    try:
        # Step 1: Ingest Data
        logger.info("Step 1: Ingesting data...")
        ingest_main()
        logger.info("Step 1: Data ingestion complete.")

        # Step 2: Align Events
        logger.info("Step 2: Aligning events...")
        align_main()
        logger.info("Step 2: Event alignment complete.")

        # Step 3: Validate Aligned Events
        logger.info("Step 3: Validating aligned events...")
        validate_main()
        logger.info("Step 3: Validation complete.")

        # Step 4: Log Data Quality
        logger.info("Step 4: Logging data quality metrics...")
        log_quality_main()
        logger.info("Step 4: Data quality logging complete.")

        # Step 5: Filter Analysis Subset
        logger.info("Step 5: Filtering analysis subset (removing recurrent storms)...")
        filter_main()
        logger.info("Step 5: Analysis subset created.")

        # Step 6: Run Statistical Analysis
        logger.info("Step 6: Running statistical analysis...")
        analysis_main()
        logger.info("Step 6: Statistical analysis complete.")

        # Step 7: Profile Pipeline
        logger.info("Step 7: Profiling pipeline performance...")
        profile_main()
        logger.info("Step 7: Profiling complete.")

        # Step 8: Versioning
        logger.info("Step 8: Updating versioning state...")
        versioning_main()
        logger.info("Step 8: Versioning update complete.")

        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Pipeline completed successfully in {duration}")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
