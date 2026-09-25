import os
import sys
import time
import socket
import urllib.request
import urllib.error
import csv
import logging
import math
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ingest_zeros.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Hardcoded canonical list of verified zeta zero sources (LMFDB/Odlyzko)
# These are the ONLY allowed sources. If unreachable, pipeline halts.
CANONICAL_ZETA_SOURCES = [
    "https://www.lmfdb.org/zeros/zeta/",
    "http://www.dtc.umn.edu/~odlyzko/doc/zeta/",
    "https://arxiv.org/list/math.NT/recent" # Fallback for recent papers if needed, but primary is LMFDB
]

# Primary data source for ingestion: LMFDB formatted CSV or direct download
# Using a direct, stable URL for the first 100,000 zeros (commonly used in research)
# Note: In a production environment, this URL should be dynamically fetched or
# a local mirror maintained. For this implementation, we use a known stable source.
# If the specific URL changes, update CANONICAL_ZETA_SOURCES and this URL.
# We will attempt to fetch from a known public repository of Odlyzko data.
ZETA_ZERO_URLS = [
    "https://www.dtc.umn.edu/~odlyzko/zeta_tables/zeros1.1", # First 100,000 zeros
    "https://www.lmfdb.org/api/zeta/zeros/?limit=100000" # LMFDB API (if available)
]

# Output file path as per spec
OUTPUT_FILE = Path("data/raw/zeta_zeros.csv")

# Maximum number of zeros to ingest (for memory safety and testing)
MAX_ZEROS = 100000

def verify_url_reachability(url: str, timeout: int = 10) -> bool:
    """
    Verifies if a URL is reachable by attempting a HEAD request.
    Returns True if reachable, False otherwise.
    """
    try:
        logger.info(f"Checking reachability of: {url}")
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                logger.info(f"URL {url} is reachable.")
                return True
            else:
                logger.warning(f"URL {url} returned status {response.status}.")
                return False
    except (urllib.error.URLError, socket.timeout, Exception) as e:
        logger.error(f"URL {url} is unreachable: {e}")
        return False

def verify_sources() -> bool:
    """
    Verifies that at least one canonical source is reachable.
    Returns True if verification passes, False otherwise.
    """
    logger.info("Verifying canonical zeta zero sources...")
    for source in CANONICAL_ZETA_SOURCES:
        if verify_url_reachability(source):
            logger.info(f"Verified source: {source}")
            return True
    
    logger.critical("CRITICAL: No canonical zeta zero sources are reachable.")
    logger.critical("Data Unavailable: Cannot proceed without verified sources.")
    return False

def parse_zeta_zero_line(line: str) -> tuple:
    """
    Parses a single line of zeta zero data.
    Expected format: index, real_part, imaginary_part (or just imaginary_part if real is 0.5)
    Returns (index, real_part, imaginary_part) or raises ValueError if malformed.
    """
    try:
        parts = line.strip().split()
        if len(parts) < 2:
            raise ValueError(f"Line too short: {line}")
        
        # Assume format: index imaginary_part (real part is 0.5 by RH assumption)
        # Some formats might be: index real_part imaginary_part
        if len(parts) == 3:
            idx = int(parts[0])
            real = float(parts[1])
            imag = float(parts[2])
        elif len(parts) == 2:
            idx = int(parts[0])
            imag = float(parts[1])
            real = 0.5 # Default to RH assumption
        else:
            raise ValueError(f"Unexpected format: {line}")
        
        return idx, real, imag
    except (ValueError, IndexError) as e:
        raise ValueError(f"Failed to parse line '{line}': {e}")

def fetch_zeta_zeros(url: str, max_count: int) -> list:
    """
    Fetches zeta zero data from a URL and parses it.
    Returns a list of tuples (index, real_part, imaginary_part).
    """
    zeros = []
    try:
        logger.info(f"Fetching data from: {url}")
        with urllib.request.urlopen(url) as response:
            # Read line by line to handle large files
            for i, line in enumerate(response):
                if i >= max_count:
                    logger.info(f"Reached max count ({max_count}). Stopping fetch.")
                    break
                
                try:
                    decoded_line = line.decode('utf-8', errors='ignore')
                    if not decoded_line.strip():
                        continue
                    idx, real, imag = parse_zeta_zero_line(decoded_line)
                    zeros.append((idx, real, imag))
                except ValueError as e:
                    logger.warning(f"Skipping malformed line {i}: {e}")
                    continue
                    
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        raise
    
    return zeros

def ingest_zeros_sample():
    """
    Ingests a sample of zeta zeros for testing purposes.
    This function is used when real data fetch fails or for quick validation.
    Note: Per task requirements, this should NOT be used as a fallback for real data.
    """
    logger.warning("Ingesting sample data for testing ONLY. Real data fetch failed.")
    # Generate a small set of sample zeros (NOT for production)
    zeros = []
    for i in range(1, 101):
        # Approximate imaginary parts of first 100 zeros (simplified)
        # Real parts are 0.5
        # These are approximate values for testing structure only
        zeros.append((i, 0.5, 14.1347 + (i-1)*1.5)) 
    return zeros

def run_pipeline():
    """
    Main pipeline for ingesting and verifying zeta zero data.
    """
    logger.info("Starting zeta zero ingestion pipeline...")
    
    # Step 1: Verify sources
    if not verify_sources():
        raise RuntimeError("Data Unavailable: Canonical zeta zero sources are unreachable.")
    
    # Step 2: Attempt to fetch real data
    zeros = []
    fetch_success = False
    
    for url in ZETA_ZERO_URLS:
        try:
            zeros = fetch_zeta_zeros(url, MAX_ZEROS)
            if zeros:
                fetch_success = True
                logger.info(f"Successfully fetched {len(zeros)} zeros from {url}")
                break
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {e}")
            continue
    
    if not fetch_success:
        # Per task requirement: FAIL LOUDLY, do not fall back to synthetic
        raise RuntimeError("Data Unavailable: Failed to fetch zeta zeros from any verified source.")
    
    # Step 3: Write to output file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['index', 'real_part', 'imaginary_part'])
        
        for idx, real, imag in zeros:
            writer.writerow([idx, f"{real:.10f}", f"{imag:.10f}"])
    
    logger.info(f"Successfully wrote {len(zeros)} zeros to {OUTPUT_FILE}")
    return len(zeros)

def main():
    """
    Entry point for the script.
    """
    try:
        count = run_pipeline()
        logger.info(f"Pipeline completed successfully. Ingested {count} zeros.")
    except RuntimeError as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
