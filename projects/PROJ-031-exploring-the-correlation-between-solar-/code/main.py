"""
Main orchestrator for the Solar Flare - Geomagnetic Storm Correlation Pipeline.
Executes steps in order: Verify Sources -> Ingest -> Align -> Filter -> Analyze.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import requests

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ingest import verify_cdaweb_source, DataFetchError, main as ingest_main
from align import main as align_main
from filter_analysis_subset import main as filter_main
from analysis import main as analysis_main
from validate import main as validate_main
from manifest_utils import load_manifest, update_source_status

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_source_heartbeat():
    """Verify all configured data sources are reachable."""
    logger.info("Starting source heartbeat verification...")
    
    # Updated URLs to match the actual working endpoints for Dst and Kp
    # Using the specific product URLs that serve text data directly
    sources = {
        "NOAA_SWPC_DST": "https://services.swpc.noaa.gov/products/noaa-dst.txt",
        "NOAA_SWPC_KP": "https://services.swpc.noaa.gov/products/noaa-kp-index.txt",
        "GOES_XRAY": "https://services.swpc.noaa.gov/products/goes-x-ray-flare-list.txt",
        "CDAWeb_LASCO": "https://cdaweb.gsfc.nasa.gov/index.html/"
    }
    
    failed_sources = []
    
    for name, url in sources.items():
        try:
            # Try HEAD first, fallback to GET
            # Some endpoints (like products) might not support HEAD properly, so we handle 404/405 by trying GET
            head_resp = requests.head(url, timeout=10, allow_redirects=True)
            if head_resp.status_code == 200:
                logger.info(f"Heartbeat OK for {name} (Status 200)")
                continue
            
            # If HEAD fails with 404 or 405, try GET immediately
            if head_resp.status_code in [404, 405, 403]:
                logger.warning(f"HEAD failed for {name} with {head_resp.status_code}, trying GET...")
                get_resp = requests.get(url, timeout=10)
                if get_resp.status_code == 200:
                    logger.info(f"Heartbeat OK for {name} (Status 200 via GET)")
                    continue
                else:
                    failed_sources.append(f"{name}: HTTP Heartbeat failed for {name}: Status {get_resp.status_code}")
                    logger.error(f"Failed to verify {name}: Status {get_resp.status_code}")
                    continue

            failed_sources.append(f"{name}: HTTP Heartbeat failed for {name}: Status {head_resp.status_code}")
            logger.error(f"Failed to verify {name}: Status {head_resp.status_code}")
            
        except requests.exceptions.RequestException as e:
            failed_sources.append(f"{name}: Connection failed - {str(e)}")
            logger.error(f"Connection failed for {name}: {str(e)}")
    
    if failed_sources:
        error_msg = "Data source heartbeat verification failed for:\n" + "\n".join(failed_sources)
        logger.error(error_msg)
        raise DataFetchError(error_msg)
    
    logger.info("All source heartbeats verified successfully.")
    return True

def run_pipeline():
    """Execute the full pipeline."""
    logger.info("=" * 60)
    logger.info("Starting Solar Flare - Geomagnetic Storm Correlation Pipeline")
    logger.info("=" * 60)
    
    try:
        # Step 1: Verify Sources
        logger.info("Step 1: Verifying data sources...")
        verify_source_heartbeat()
        
        # Step 2: Ingest & Stream
        logger.info("Step 2: Ingesting data...")
        if not ingest_main():
            raise RuntimeError("Ingestion step failed")
        
        # Step 3: Align
        logger.info("Step 3: Aligning events...")
        if not align_main():
            raise RuntimeError("Alignment step failed")
        
        # Step 4: Filter Non-Recurrent
        logger.info("Step 4: Filtering non-recurrent storms...")
        if not filter_main():
            raise RuntimeError("Filtering step failed")
        
        # Step 5: Analyze
        logger.info("Step 5: Performing analysis...")
        if not analysis_main():
            raise RuntimeError("Analysis step failed")
        
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return False

def main():
    """Entry point."""
    success = run_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()