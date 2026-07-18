"""
Ingest Riemann Zeta zeros from verified external sources (LMFDB, Odlyzko).
Implements Constitution Principle II: Hardcoded verified sources only.
Fails loudly if sources are unreachable; never falls back to synthetic data.
"""
import os
import sys
import time
import socket
import urllib.request
import urllib.error
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Import project utilities based on API surface
from src.utils.config import get_project_paths
from src.utils.io import load_state, save_state, update_state_checksums
from src.utils.models import ZetaZero

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardcoded Verified Sources (Constitution Principle II)
# LMFDB API endpoint for first N non-trivial zeros
LMFDB_URL = "https://www.lmfdb.org/api/riemann/zeta_zeros?limit=1000"
# Odlyzko dataset mirror (University of Minnesota) - raw text format
ODLYZKO_URL = "https://www.dtc.umn.edu/~odlyzko/doc/zeta.function/zeta.1000000.txt"

# State file path
STATE_FILE_NAME = "PROJ-548-exploring-the-relationship-between-prime.yaml"

def verify_url_reachability(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Verifies if a URL is reachable and returns a status message.
    Returns (True, "OK") or (False, error_message).
    """
    try:
        logger.info(f"Checking reachability of: {url}")
        # Perform a HEAD request first to check existence without downloading full body
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'llmXive-Research-Agent/1.0')
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if status_code == 200:
                return True, "Reachable"
            else:
                return False, f"HTTP Error: {status_code}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except socket.timeout:
        return False, "Connection timed out"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def verify_sources() -> Dict[str, Any]:
    """
    Verifies all hardcoded sources defined in the module.
    Returns a dictionary of verification results.
    """
    results = {}
    all_healthy = True

    sources = [
        ("LMFDB API", LMFDB_URL),
        ("Odlyzko Dataset", ODLYZKO_URL)
    ]

    for name, url in sources:
        reachable, message = verify_url_reachability(url)
        results[name] = {
            "url": url,
            "reachable": reachable,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        if not reachable:
            all_healthy = False
            logger.warning(f"Source '{name}' is unreachable: {message}")
        else:
            logger.info(f"Source '{name}' is healthy.")

    return {
        "verification_successful": all_healthy,
        "sources": results
    }

def parse_zeta_zero_line(line: str) -> Optional[ZetaZero]:
    """
    Parses a line from the Odlyzko dataset.
    Format expected: index, real_part, imaginary_part (or similar depending on source).
    For LMFDB JSON, this would be handled differently, but this function targets
    the text-based Odlyzko format primarily for streaming.
    """
    try:
        parts = line.strip().split()
        if len(parts) < 2:
            return None
        
        # Odlyzko format typically: index, imaginary_part
        # We assume the real part is 0.5 for non-trivial zeros on the critical line
        index = int(parts[0])
        gamma = float(parts[1])
        
        return ZetaZero(
            index=index,
            real_part=0.5,
            imaginary_part=gamma
        )
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse line: {line} - {e}")
        return None

def ingest_zeros_sample(output_path: Path, limit: Optional[int] = None) -> int:
    """
    Fetches zeta zeros from the verified sources and writes them to a CSV file.
    
    Priority:
    1. Try Odlyzko (text stream) for bulk data if available.
    2. Fallback to LMFDB API if Odlyzko fails (though both must be reachable per spec).
    
    If both are unreachable, this function raises a RuntimeError.
    """
    if not verify_sources()["verification_successful"]:
        raise RuntimeError(
            "CRITICAL: Verified data sources are unreachable. "
            "Cannot proceed without real data per Constitution Principle II."
        )

    zeros: List[ZetaZero] = []
    count = 0

    # Strategy: Try to stream from Odlyzko first (bulk text)
    logger.info(f"Attempting to fetch from Odlyzko: {ODLYZKO_URL}")
    try:
        req = urllib.request.Request(ODLYZKO_URL)
        req.add_header('User-Agent', 'llmXive-Research-Agent/1.0')
        
        with urllib.request.urlopen(req, timeout=60) as response:
            # Read line by line to handle large files without loading all into memory
            for line in response:
                line_str = line.decode('utf-8', errors='ignore')
                if not line_str.strip():
                    continue
                
                zero = parse_zeta_zero_line(line_str)
                if zero:
                    zeros.append(zero)
                    count += 1
                    if limit and count >= limit:
                        break
                    
                    # Log progress every 1000 zeros
                    if count % 1000 == 0:
                        logger.info(f"Fetched {count} zeros...")
                        
    except Exception as e:
        logger.error(f"Failed to fetch from Odlyzko: {e}")
        # If Odlyzko fails during fetch (after reachability check), try LMFDB
        logger.info("Falling back to LMFDB API...")
        try:
            req = urllib.request.Request(LMFDB_URL)
            req.add_header('User-Agent', 'llmXive-Research-Agent/1.0')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                import json
                data = json.loads(response.read().decode('utf-8'))
                # LMFDB returns a list of zeros under 'zeros' key usually
                # Structure varies, assuming standard API response
                zero_list = data.get('zeros', [])
                
                for i, z in enumerate(zero_list):
                    if limit and count >= limit:
                        break
                    
                    # LMFDB API might return 'im' for imaginary part
                    gamma = float(z.get('im', z.get('imaginary_part', 0)))
                    zeros.append(ZetaZero(
                        index=i+1,
                        real_part=0.5,
                        imaginary_part=gamma
                    ))
                    count += 1
        except Exception as e2:
            raise RuntimeError(
                f"CRITICAL: Both Odlyzko and LMFDB sources failed during fetch. "
                f"Odlyzko error: {e}, LMFDB error: {e2}. "
                "Pipeline cannot proceed without real data."
            )

    if count == 0:
        raise RuntimeError("CRITICAL: No zeros were retrieved from any verified source.")

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Writing {count} zeros to {output_path}")
    
    with open(output_path, 'w', newline='') as f:
        f.write("index,real_part,imaginary_part\n")
        for z in zeros:
            f.write(f"{z.index},{z.real_part},{z.imaginary_part}\n")

    return count

def run_pipeline(limit: Optional[int] = 10000) -> None:
    """
    Main entry point for the ingestion pipeline.
    1. Verify sources.
    2. Ingest data.
    3. Update state file with verification status and checksum.
    """
    paths = get_project_paths()
    state_path = paths['state'] / STATE_FILE_NAME
    output_csv = paths['processed'] / "zeta_zeros.csv"

    logger.info("Starting Zeta Zero Ingestion Pipeline (T013a)")

    # Step 1: Verify Sources
    verification_result = verify_sources()
    
    if not verification_result["verification_successful"]:
        logger.error("Source verification failed. Halting pipeline.")
        # Update state to reflect failure
        state = load_state(state_path)
        state['t013a'] = {
            "status": "failed",
            "reason": "Verified sources unreachable",
            "details": verification_result
        }
        save_state(state_path, state)
        raise RuntimeError("Pipeline halted: Verified sources unreachable.")

    # Step 2: Ingest Data
    try:
        count = ingest_zeros_sample(output_csv, limit=limit)
        logger.info(f"Successfully ingested {count} zeros.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        state = load_state(state_path)
        state['t013a'] = {
            "status": "failed",
            "reason": str(e),
            "details": verification_result
        }
        save_state(state_path, state)
        raise

    # Step 3: Update State
    state = load_state(state_path)
    state['t013a'] = {
        "status": "completed",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources_verified": verification_result,
        "output_file": str(output_csv),
        "count": count
    }
    
    # Update checksums for the new data file
    update_state_checksums(state, paths['processed'])
    
    save_state(state_path, state)
    logger.info("Pipeline completed successfully. State updated.")

if __name__ == "__main__":
    run_pipeline()
