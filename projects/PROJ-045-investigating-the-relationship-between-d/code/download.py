"""
Data Download Module for PROJ-045.

Handles fetching crystal structures from OBELiX and Materials Project.
Implements robust error handling with retry logic and exponential backoff.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# Import existing models if needed for validation, though raw data fetching is primary here
# from models import ElectrolyteComposition # Optional: can be used for strict typing later

# Configure module logger
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 5
BASE_BACKOFF = 2.0  # seconds
TIMEOUT_SECONDS = 30

# Static MP-ID list for the high-fidelity subset (as per T014)
# These are representative solid electrolytes: LLZO, LATP, LGPS, etc.
STATIC_MP_IDS = [
    "mp-1234567",  # Placeholder for real MP-IDs to be populated from spec/data
    "mp-761628",   # Li7La3Zr2O12 (LLZO) example
    "mp-568679",   # Li1.3Al0.3Ti1.7(PO4)3 (LATP) example
    "mp-1072974",  # Li10GeP2S12 (LGPS) example - note: might need sulfide handling
]

# OBELiX API Configuration (Mocked for now, but structure ready for real endpoint)
OBELiX_BASE_URL = os.getenv("OBELiX_API_URL", "https://api.obelix-db.org/v1")
MP_API_KEY = os.getenv("MP_API_KEY", "")
MP_API_URL = "https://rest.materialsproject.org"


def setup_download_logging() -> logging.Logger:
    """Initialize logging for the download module."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    return logger


def _exponential_backoff(attempt: int) -> float:
    """Calculate exponential backoff delay."""
    delay = BASE_BACKOFF * (2 ** attempt)
    # Add jitter to prevent thundering herd
    jitter = delay * 0.1 * (hash(str(time.time())) % 100 / 100)
    return delay + jitter


def _fetch_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = TIMEOUT_SECONDS
) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a URL with retry logic and exponential backoff.

    Args:
        url: Target URL
        params: Query parameters
        headers: Request headers
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response or None if all retries fail.
    """
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} for {url}")
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except (Timeout, ConnectionError) as e:
            last_exception = e
            delay = _exponential_backoff(attempt)
            logger.warning(f"Network error ({e}). Retrying in {delay:.2f}s...")
            time.sleep(delay)
        except RequestException as e:
            # Non-retryable errors (e.g., 404, 403) should not retry
            logger.error(f"Request failed with status {getattr(e.response, 'status_code', 'N/A')}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts. Last error: {last_exception}")
    return None


def fetch_mp_structure(mp_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch crystal structure data from Materials Project.

    Args:
        mp_id: Materials Project ID (e.g., 'mp-123456')

    Returns:
        Dictionary containing structure data (CIF, POSCAR, or JSON) or None.
    """
    if not MP_API_KEY:
        logger.warning("MP_API_KEY not set. Skipping Materials Project fetch.")
        return None

    headers = {"X-API-Key": MP_API_KEY}
    url = f"{MP_API_URL}/materials/{mp_id}/summary"

    # Requesting structure data specifically
    params = {"fields": "structure,material_id,pretty_formula"}

    data = _fetch_with_retry(url, params=params, headers=headers)

    if data and "data" in data:
        return data["data"]
    return None


def fetch_obelix_structure(composition_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch crystal structure data from OBELiX.

    Args:
        composition_id: Unique identifier in OBELiX database.

    Returns:
        Dictionary containing structure data or None.
    """
    # Construct URL based on environment or default
    url = f"{OBELiX_BASE_URL}/structures/{composition_id}"

    # OBELiX might not require auth for public read, but handle headers if needed
    headers = {"Accept": "application/json"}

    data = _fetch_with_retry(url, headers=headers)

    if data:
        return data
    return None


def save_structure(data: Dict[str, Any], output_path: Path, format: str = "json") -> bool:
    """
    Save structure data to disk.

    Args:
        data: The structure data dictionary.
        output_path: Path to save the file.
        format: Output format ('json', 'cif', 'poscar').

    Returns:
        True if successful, False otherwise.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if format == "json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        elif format == "cif":
            # Assuming data contains CIF string or we construct it
            if "cif" in data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(data["cif"])
            else:
                logger.error("CIF format requested but data does not contain 'cif' key.")
                return False
        elif format == "poscar":
            if "poscar" in data:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(data["poscar"])
            else:
                logger.error("POSCAR format requested but data does not contain 'poscar' key.")
                return False
        else:
            logger.error(f"Unsupported format: {format}")
            return False

        logger.info(f"Saved structure to {output_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to write file {output_path}: {e}")
        return False


def download_all_structures() -> Dict[str, Any]:
    """
    Main orchestration function to download all structures.
    Iterates through static lists and saves results.

    Returns:
        Dictionary summarizing download status.
    """
    logger.info("Starting bulk download of crystal structures.")
    results = {
        "materials_project": [],
        "obelix": [],
        "failed": [],
        "total_downloaded": 0
    }

    # 1. Download from Materials Project
    for mp_id in STATIC_MP_IDS:
        logger.info(f"Fetching Materials Project ID: {mp_id}")
        data = fetch_mp_structure(mp_id)
        if data:
            filename = f"{mp_id}.json"
            output_path = Path("data/raw/structures/mp") / filename
            if save_structure(data, output_path, format="json"):
                results["materials_project"].append(mp_id)
                results["total_downloaded"] += 1
            else:
                results["failed"].append({"id": mp_id, "source": "MP", "reason": "Save failed"})
        else:
            results["failed"].append({"id": mp_id, "source": "MP", "reason": "Fetch failed"})

    # 2. Download from OBELiX (Example IDs - these would come from a config or spec)
    # Using placeholder IDs for demonstration of the retry logic flow
    obelix_ids = ["OBEL-001", "OBEL-002"] # Replace with real IDs if available in spec
    for ob_id in obelix_ids:
        logger.info(f"Fetching OBELiX ID: {ob_id}")
        data = fetch_obelix_structure(ob_id)
        if data:
            filename = f"{ob_id}.json"
            output_path = Path("data/raw/structures/obelix") / filename
            if save_structure(data, output_path, format="json"):
                results["obelix"].append(ob_id)
                results["total_downloaded"] += 1
            else:
                results["failed"].append({"id": ob_id, "source": "OBELiX", "reason": "Save failed"})
        else:
            results["failed"].append({"id": ob_id, "source": "OBELiX", "reason": "Fetch failed"})

    logger.info(f"Download complete. Total successful: {results['total_downloaded']}, Failed: {len(results['failed'])}")
    return results


def main():
    """Entry point for the download script."""
    setup_download_logging()
    results = download_all_structures()

    # Save a summary report
    report_path = Path("data/processed/download_summary.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Summary report saved to {report_path}")

    # Exit with error code if critical failures occurred (optional policy)
    if results["total_downloaded"] == 0:
        logger.error("No structures were downloaded. Check network or API keys.")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()