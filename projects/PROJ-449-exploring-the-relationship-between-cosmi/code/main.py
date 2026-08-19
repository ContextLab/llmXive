"""
Main entry point for the cosmic ray composition vs solar activity analysis pipeline.

Orchestrates the full data pipeline:
1. Fetch AMS-02 cosmic ray flux data
2. Fetch NOAA sunspot data
3. Align and merge datasets
4. Calculate composition ratios
5. Perform correlation analysis
6. Generate visualizations and reports
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.logging import setup_logger
from code.utils.config import CONFIG
from code.data.fetch_ams02 import fetch_species_data, main as fetch_ams02_main
from code.data.fetch_noaa import fetch_noaa_sunspots, main as fetch_noaa_main
from code.data.align_data import main as align_data_main
from code.data.preprocess import main as preprocess_main
from code.analysis.correlation import main as correlation_main
from code.analysis.visualization import main as visualization_main
from code.analysis.bootstrap import main as bootstrap_main
from code.analysis.model_fitting import main as model_fitting_main

def main():
    """Run the complete analysis pipeline."""
    logger = setup_logger("pipeline")
    logger.info("Starting cosmic ray composition vs solar activity analysis")

    try:
        # Step 1: Fetch data
        logger.info("Step 1: Fetching AMS-02 data")
        fetch_ams02_main()

        logger.info("Step 2: Fetching NOAA sunspot data")
        fetch_noaa_main()

        # Step 2: Align and merge
        logger.info("Step 3: Aligning and merging datasets")
        align_data_main()

        # Step 3: Preprocess and calculate ratios
        logger.info("Step 4: Calculating composition ratios")
        preprocess_main()

        # Step 4: Correlation analysis
        logger.info("Step 5: Performing correlation analysis")
        correlation_main()

        # Step 5: Bootstrap validation
        logger.info("Step 6: Running bootstrap resampling")
        bootstrap_main()

        # Step 6: Model fitting
        logger.info("Step 7: Fitting diffusion model")
        model_fitting_main()

        # Step 7: Visualization
        logger.info("Step 8: Generating visualizations")
        visualization_main()

        logger.info("Pipeline completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
