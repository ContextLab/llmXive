"""
Main orchestration script for the Solar Flare - Geomagnetic Storm Correlation Pipeline.

This script executes the full pipeline as defined in the run-book (quickstart.md).
It coordinates data ingestion, alignment, filtering, analysis, and validation.

Execution Order:
1. Verify Sources (Heartbeat Check) - T064
2. Ingest raw data (NOAA SWPC, CDAWeb)
3. Align events (Solar Flares, CMEs, Geomagnetic Storms)
4. Validate aligned events
5. Log data quality
6. Filter for analysis subset (remove recurrent storms)
7. Run statistical analysis
8. Validate metrics
9. Profile pipeline performance
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import requests

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import pipeline modules
from ingest import main as ingest_main, DataFetchError
from align import main as align_main
from validate import main as validate_main
from log_data_quality import main as log_quality_main
from filter_analysis_subset import main as filter_main
from analysis import main as analysis_main
from profiler import main as profile_main
from versioning import main as versioning_main

# Setup logging
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "pipeline_run.log")
    ]
)
logger = logging.getLogger("Pipeline")

# Data Sources Configuration for Heartbeat
DATA_SOURCES = {
    "NOAA_SWPC_FTP": "ftp://ftp.swpc.noaa.gov/pub/lists/",
    "NOAA_SWPC_DST": "https://www.swpc.noaa.gov/products/dst-index",
    "NOAA_SWPC_KP": "https://www.swpc.noaa.gov/products/kp-index",
    "CDAWeb_LASCO": "https://cdaweb.gsfc.nasa.gov/index.html/"
}

def verify_source_heartbeat(name: str, url: str) -> bool:
    """
    Attempts to fetch a single "heartbeat" record from a data source.
    Returns True if successful, raises DataFetchError if not.
    """
    try:
        logger.info(f"Verifying heartbeat for {name}: {url}")
        
        if url.startswith("ftp://"):
            # For FTP, we try to list a directory or fetch a known small file.
            # Since requests doesn't support FTP well, we'll use a simple socket check
            # or assume the URL is valid if it starts with ftp and we can connect.
            # However, for robustness in this script, we will attempt a HEAD request
            # to the base URL if possible, or just check connectivity.
            # Given the constraints, we will simulate a "ping" by checking if the host is reachable.
            # A more robust way for FTP is to use ftplib, but we stick to requests for HTTP.
            # For this heartbeat, we will check the HTTP equivalent if available, 
            # or skip strict FTP verification if no HTTP mirror exists, 
            # but the task requires a check.
            # We will try to connect to the FTP host to see if it's alive.
            import socket
            host = url.replace("ftp://", "").split("/")[0]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            try:
                sock.connect((host, 21))
                sock.close()
                logger.info(f"Heartbeat OK for {name} (FTP Port 21 reachable)")
                return True
            except socket.error as e:
                raise DataFetchError(f"FTP Heartbeat failed for {name}: {e}")
        else:
            # HTTP/HTTPS sources
            response = requests.head(url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                logger.info(f"Heartbeat OK for {name} (Status {response.status_code})")
                return True
            else:
                # Some sites return 405 for HEAD, try GET with stream
                logger.warning(f"HEAD failed for {name} with {response.status_code}, trying GET...")
                resp_get = requests.get(url, timeout=10, stream=True)
                if resp_get.status_code == 200:
                    logger.info(f"Heartbeat OK for {name} (Status {resp_get.status_code})")
                    return True
                else:
                    raise DataFetchError(f"HTTP Heartbeat failed for {name}: Status {resp_get.status_code}")
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Heartbeat check failed for {name}: {e}")

def run_pipeline():
    """Execute the full pipeline steps."""
    logger.info("Starting Solar Flare - Geomagnetic Storm Correlation Pipeline")
    start_time = datetime.now()

    try:
        # Step 0: Verify Sources (Heartbeat Check) - T064
        logger.info("Step 0: Verifying data source connectivity (Heartbeat)...")
        failed_sources = []
        for name, url in DATA_SOURCES.items():
            try:
                verify_source_heartbeat(name, url)
            except DataFetchError as e:
                failed_sources.append(f"{name}: {e}")
        
        if failed_sources:
            error_msg = "Data source heartbeat verification failed for:\n" + "\n".join(failed_sources)
            logger.error(error_msg)
            raise DataFetchError(error_msg)
        
        logger.info("Step 0: All data sources verified.")

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

    except DataFetchError as e:
        logger.error(f"Pipeline failed due to data source issues: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()