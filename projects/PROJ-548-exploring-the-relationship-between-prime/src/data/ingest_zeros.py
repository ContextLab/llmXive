"""
Ingests Riemann Zeta zeros from verified sources (LMFDB/Odlyzko).
Implements data validation, malformed entry skipping with warnings,
and strict pipeline halting on verification failure.
"""
import os
import sys
import time
import socket
import urllib.request
import urllib.error
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Generator

# Import from project utils
from src.utils.io import load_state, save_state, compute_file_checksum
from src.utils.models import ZetaZero

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STATE_FILE = Path("state.yaml")
DATA_DIR = Path("data/processed")
OUTPUT_FILE = DATA_DIR / "zeta_zeros.csv"
VERIFIED_SOURCES = {
    "lmfdb": "https://www.lmfdb.org/Zero/1.2.1.1",
    "odlyzko": "https://www.dtc.umn.edu/~odlyzko/doc/zeta.zeros/"
}

def parse_zeta_zero_line(line: str, line_num: int) -> Optional[ZetaZero]:
    """
    Parses a single line of zeta zero data.
    Expected format: t, gamma, (optional metadata)
    Returns ZetaZero object or None if malformed.
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    try:
        # Handle various delimiters (comma, space, tab)
        parts = re.split(r'[\s,]+', line)
        if len(parts) < 2:
            logger.warning(f"Skipping malformed line {line_num}: insufficient columns")
            return None

        # Extract imaginary part (gamma) and real part (t, usually 0.5)
        # Standard format often: t, gamma
        # If only gamma is provided, assume t=0.5
        if len(parts) >= 2:
            t_val = float(parts[0])
            gamma_val = float(parts[1])
        else:
            # Fallback if only gamma is present (common in some datasets)
            t_val = 0.5
            gamma_val = float(parts[0])

        return ZetaZero(t=t_val, gamma=gamma_val)

    except ValueError as e:
        logger.warning(f"Skipping malformed line {line_num}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing line {line_num}: {e}")
        return None

def verify_url_reachability(url: str, timeout: int = 10) -> bool:
    """Checks if a URL is reachable."""
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(request, timeout=timeout)
        return True
    except (urllib.error.URLError, socket.timeout, socket.gaierror) as e:
        logger.warning(f"URL unreachable: {url} - {e}")
        return False

def verify_sources() -> Dict[str, bool]:
    """Verifies all configured sources are reachable."""
    results = {}
    for name, url in VERIFIED_SOURCES.items():
        logger.info(f"Verifying source: {name} ({url})")
        reachable = verify_url_reachability(url)
        results[name] = reachable
        if not reachable:
            logger.error(f"CRITICAL: Source {name} is unreachable.")
    return results

def load_state() -> Dict[str, Any]:
    """Loads state from YAML file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            import yaml
            return yaml.safe_load(f) or {}
    return {"verification_status": {}, "checksums": {}}

def save_state(state: Dict[str, Any]) -> None:
    """Saves state to YAML file."""
    with open(STATE_FILE, 'w') as f:
        import yaml
        yaml.dump(state, f)

def ingest_zeros_sample(
    source: str = "lmfdb",
    limit: Optional[int] = 1000,
    output_path: Optional[Path] = None
) -> Tuple[int, int]:
    """
    Ingests zeta zeros from a verified source.
    Validates data, skips malformed entries, and writes to CSV.
    Returns (total_processed, valid_count).
    """
    if output_path is None:
        output_path = OUTPUT_FILE

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Verify source first
    if source not in VERIFIED_SOURCES:
        raise ValueError(f"Unknown source: {source}. Available: {list(VERIFIED_SOURCES.keys())}")

    url = VERIFIED_SOURCES[source]
    logger.info(f"Starting ingestion from {source} at {url}")

    # Check reachability
    if not verify_url_reachability(url):
        raise RuntimeError(f"Pipeline halted: Source {source} ({url}) is unreachable. "
                           f"Verification failed as per Constitution Principle II.")

    valid_count = 0
    total_processed = 0
    skipped_count = 0
    zeros: List[ZetaZero] = []

    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=30) as response:
            # Decode chunk by chunk to handle large files
            for chunk in iter(lambda: response.read(4096), b''):
                text_chunk = chunk.decode('utf-8', errors='ignore')
                lines = text_chunk.splitlines()

                for line in lines:
                    total_processed += 1
                    if limit and total_processed > limit:
                        break

                    parsed = parse_zeta_zero_line(line, total_processed)
                    if parsed:
                        zeros.append(parsed)
                        valid_count += 1
                    else:
                        skipped_count += 1

                    if total_processed % 10000 == 0:
                        logger.info(f"Processed {total_processed} lines, {valid_count} valid, {skipped_count} skipped")

                    if limit and valid_count >= limit:
                        break

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP Error {e.code} from {url}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data from {url}: {e}")

    if valid_count == 0:
        raise RuntimeError(f"Pipeline halted: No valid zeta zero entries found from {source}. "
                           f"Data validation failed.")

    # Write to CSV
    logger.info(f"Writing {valid_count} valid entries to {output_path}")
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['t', 'gamma'])
        for z in zeros:
            writer.writerow([z.t, z.gamma])

    # Update state
    state = load_state()
    if "verification_status" not in state:
        state["verification_status"] = {}
    state["verification_status"][source] = {
        "status": "success",
        "timestamp": time.time(),
        "valid_count": valid_count,
        "skipped_count": skipped_count,
        "total_processed": total_processed
    }
    state["checksums"][str(output_path)] = compute_file_checksum(output_path)
    save_state(state)

    logger.info(f"Ingestion complete: {valid_count} valid, {skipped_count} skipped.")
    return total_processed, valid_count

def run_pipeline() -> None:
    """
    Main entry point for the zeta zero ingestion pipeline.
    Performs verification, ingestion, and validation.
    """
    logger.info("Starting Zeta Zero Ingestion Pipeline")

    # 1. Verify Sources
    logger.info("Step 1: Verifying source reachability...")
    status = verify_sources()
    if not all(status.values()):
        failed_sources = [k for k, v in status.items() if not v]
        error_msg = f"Pipeline halted: Verification failed for sources: {failed_sources}. " \
                    f"Cannot proceed without verified data sources (Constitution Principle II)."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # 2. Ingest Data
    # Defaulting to LMFDB for the sample run, but could be parameterized
    try:
        ingest_zeros_sample(source="lmfdb", limit=10000)
    except RuntimeError as e:
        logger.error(f"Pipeline halted during ingestion: {e}")
        raise

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    run_pipeline()
