"""
Ingestion wrapper script for T048.
Executes data download and merge logic.
"""
import logging
import sys
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download import download_lsms_batch, download_nasa_power_batch, download_faostat_batch
from data.clean import run_sampling_pipeline, clean_and_merge
from utils.logging import initialize_logging

logger = initialize_logging()

def main():
    logger.log("start_ingestion")
    try:
        # 1. Download
        logger.log("step_download_lsms")
        download_lsms_batch()
        
        logger.log("step_download_climate")
        download_nasa_power_batch()
        
        logger.log("step_download_faostat")
        download_faostat_batch()

        # 2. Clean and Merge (T016)
        logger.log("step_clean_merge")
        clean_and_merge()

        # 3. Sampling (T018)
        logger.log("step_sampling")
        run_sampling_pipeline()

        logger.log("end_ingestion", status="success")
    except Exception as e:
        logger.log("end_ingestion", status="failed", error=str(e))
        raise

if __name__ == "__main__":
    main()
