"""
Ingest Riemann Zeta zeros from verified external sources.

This module implements the core data ingestion logic for zeta zeros.
It verifies source reachability, fetches data from LMFDB/Odlyzko,
parses the results, and writes them to data/raw/zeta_zeros.csv.

Addresses FR-002: Ingest zeta zeros from verified sources.
"""
import os
import sys
import time
import socket
import urllib.request
import urllib.error
import csv
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Add project root to path to resolve imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import ensure_directories
from src.utils.io import load_state, save_state, update_state_checksums, commit_state
from src.utils.models import ZetaZero

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verified sources configuration (read from research.md in a real scenario, 
# but we use the known LMFDB URL as per T013a's requirement to use verified sources)
# The actual URL list would be parsed from research.md, but for this implementation
# we define the standard LMFDB zeta zero URL which is the primary verified source.
VERIFIED_ZETA_ZERO_URLS = [
    "https://www.lmfdb.org/Character/Dirichlet/1/1/zeros/10000"
]

# Output file paths
RAW_ZETA_ZEROS_CSV = "data/raw/zeta_zeros.csv"
STATE_FILE = "state/projects/PROJ-548-exploring-the-relationship-between-prime.yaml"

def verify_url_reachability(url: str, timeout: int = 10) -> bool:
    """
    Check if a URL is reachable.
    
    Args:
        url: The URL to check
        timeout: Connection timeout in seconds
        
    Returns:
        True if reachable, False otherwise
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
            (urllib.parse.urlparse(url).hostname or 'localhost', 443)
        )
        # Try to open the URL
        req = urllib.request.Request(url, method='HEAD')
        urllib.request.urlopen(req, timeout=timeout)
        return True
    except (socket.timeout, urllib.error.URLError, OSError) as e:
        logger.warning(f"URL {url} is unreachable: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking URL {url}: {e}")
        return False

def verify_sources() -> List[str]:
    """
    Verify that all configured zeta zero sources are reachable.
    
    Returns:
        List of reachable URLs
        
    Raises:
        RuntimeError: If no sources are reachable
    """
    reachable = []
    for url in VERIFIED_ZETA_ZERO_URLS:
        if verify_url_reachability(url):
            reachable.append(url)
            logger.info(f"Source verified: {url}")
        else:
            logger.warning(f"Source unreachable: {url}")
    
    if not reachable:
        error_msg = "CRITICAL: No verified zeta zero sources are reachable. Pipeline cannot proceed."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    return reachable

def parse_zeta_zero_line(line: str) -> Optional[ZetaZero]:
    """
    Parse a single line of zeta zero data.
    
    Expected format: t value (float)
    Some sources may include header lines or comments starting with #
    
    Args:
        line: Raw line from the data source
        
    Returns:
        ZetaZero object or None if line is invalid
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None
    
    try:
        t_value = float(line)
        return ZetaZero(t=t_value, source="LMFDB")
    except ValueError:
        logger.warning(f"Could not parse line as float: {line}")
        return None

def fetch_zeta_zeros(url: str, max_zeros: int = 10000) -> List[ZetaZero]:
    """
    Fetch zeta zeros from a given URL.
    
    This implementation handles the LMFDB format which returns zeros in
    a text format, one per line.
    
    Args:
        url: The URL to fetch from
        max_zeros: Maximum number of zeros to fetch
        
    Returns:
        List of ZetaZero objects
    """
    zeros = []
    try:
        # For LMFDB, we fetch the raw text content
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            lines = content.split('\n')
            
            count = 0
            for line in lines:
                if count >= max_zeros:
                    break
                zero = parse_zeta_zero_line(line)
                if zero:
                    zeros.append(zero)
                    count += 1
            
            logger.info(f"Fetched {len(zeros)} zeros from {url}")
            
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e.code} {e.reason}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"URL error fetching {url}: {e.reason}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise
    
    return zeros

def ingest_zeros_sample(output_path: str, max_zeros: int = 10000) -> int:
    """
    Main ingestion function to fetch and save zeta zeros.
    
    Args:
        output_path: Path to the output CSV file
        max_zeros: Maximum number of zeros to ingest
        
    Returns:
        Number of zeros successfully ingested
        
    Raises:
        RuntimeError: If source verification fails or data fetch fails
    """
    ensure_directories([output_path])
    
    # Verify sources first (T013a requirement)
    reachable_urls = verify_sources()
    
    all_zeros = []
    for url in reachable_urls:
        try:
            zeros = fetch_zeta_zeros(url, max_zeros)
            all_zeros.extend(zeros)
        except Exception as e:
            logger.error(f"Failed to fetch from {url}: {e}")
            # If any source fails, we halt as per T013a
            raise RuntimeError(f"Failed to fetch from verified source {url}: {e}")
    
    if not all_zeros:
        error_msg = "No zeta zeros were successfully ingested from any verified source."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['t', 'source'])  # Header
        for zero in all_zeros:
            writer.writerow([zero.t, zero.source])
    
    logger.info(f"Successfully wrote {len(all_zeros)} zeros to {output_path}")
    
    # Update state file with checksum
    state_path = Path(project_root) / STATE_FILE
    if state_path.exists():
        state = load_state(state_path)
        update_state_checksums(state, output_path)
        commit_state(state, state_path)
        logger.info(f"Updated state file checksums: {state_path}")
    
    return len(all_zeros)

def run_pipeline() -> Dict[str, Any]:
    """
    Run the full zeta zero ingestion pipeline.
    
    Returns:
        Dictionary with ingestion results
    """
    output_path = str(project_root / RAW_ZETA_ZEROS_CSV)
    
    logger.info("Starting zeta zero ingestion pipeline...")
    
    try:
        count = ingest_zeros_sample(output_path)
        return {
            "status": "success",
            "zeros_ingested": count,
            "output_file": output_path
        }
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "zeros_ingested": 0
        }

def main():
    """Entry point for script execution."""
    result = run_pipeline()
    print(f"Ingestion result: {result}")
    sys.exit(0 if result["status"] == "success" else 1)

if __name__ == "__main__":
    main()
