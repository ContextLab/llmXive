import os
import sys
import logging
import argparse
from pathlib import Path

def setup_logging_pipeline():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def run_stage(stage_function):
    try:
        stage_function()
        return True
    except Exception as e:
        logging.error(f"Stage failed: {e}")
        return False

def run_full_pipeline():
    # Import stage functions
    from data.ingest import main as ingest_main
    from data.descriptors import main as descriptors_main
    from data.clean import main as clean_main
    from data.exclusion_report import main as exclusion_report_main
    from data.finalize_dataset import main as finalize_main
    from data.split import main as split_main

    logger = setup_logging_pipeline()
    logger.info("Starting the full pipeline.")

    # 1. Ingest Data
    if not run_stage(ingest_main):
        return False

    # 2. Compute Descriptors
    if not run_stage(descriptors_main):
        return False

    # 3. Clean and Filter Data
    if not run_stage(clean_main):
        return False

    # 4. Aggregate Exclusion Logs and Generate Report
    if not run_stage(exclusion_report_main):
        return False

    # 5. Finalize Dataset (Calculate success rate, save checksum)
    if not run_stage(finalize_main):
        return False

    # 6. Split Dataset
    if not run_stage(split_main):
        return False

    logger.info("Pipeline completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the SN1 reaction rate constant prediction pipeline.")
    parser.add_argument("--run_all", action="store_true", help="Run all stages of the pipeline.")
    args = parser.parse_args()

    logger = setup_logging_pipeline()

    if args.run_all or len(sys.argv) == 1:  # Run all stages if --run_all is specified or no arguments are given
        success = run_full_pipeline()
        if not success:
            logger.error("Pipeline failed.")
            sys.exit(1)
        else:
            sys.exit(0)

    else:
        logger.warning("No stage specified, exiting")
        sys.exit(0)


if __name__ == "__main__":
    main()
