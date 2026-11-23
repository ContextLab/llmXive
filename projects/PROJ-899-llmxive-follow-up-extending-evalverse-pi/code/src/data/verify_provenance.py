"""
Provenance verification for the EvalVerse dataset.

This module checks that the downloaded dataset's metadata matches the
expected DATASET_DOI and DATASET_URL defined in src/config.py.
It ensures data integrity and prevents data drift from source updates.
"""

import os
import sys
import json
import logging
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import project configuration and utilities
from src.config import get_project_root, get_data_root, get_state_root, DATASET_DOI, DATASET_URL
from src.utils import get_logger, ensure_directories, write_json, read_json

# Configure logger
logger = get_logger(__name__)


def check_url_reachable(url: str, timeout: int = 10) -> Tuple[bool, Optional[str]]:
    """
    Check if a URL is reachable and returns a status code.

    Args:
        url: The URL to check.
        timeout: Connection timeout in seconds.

    Returns:
        Tuple of (is_reachable, error_message).
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                return True, None
            else:
                return False, f"URL returned status code {response.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def extract_doi_from_url(url: str) -> Optional[str]:
    """
    Attempt to extract a DOI from a URL string.
    Common patterns: https://doi.org/10.xxxx/xxxxx, https://zenodo.org/record/xxxxx

    Args:
        url: The URL to parse.

    Returns:
        Extracted DOI string or None if not found.
    """
    if not url:
        return None

    # Pattern 1: doi.org URL
    if "doi.org" in url:
        parts = url.split("doi.org/")
        if len(parts) > 1:
            return parts[1].strip("/")

    # Pattern 2: Zenodo record URL (convert to DOI format if possible)
    if "zenodo.org" in url:
        if "/record/" in url:
            # Zenodo URLs don't directly contain DOI, but we can check consistency
            # by comparing the record ID if we have a mapping, or just note the mismatch
            pass

    return None


def verify_provenance() -> Dict[str, Any]:
    """
    Verify that the downloaded dataset matches the expected provenance.

    This function:
    1. Checks if the dataset URL is reachable.
    2. Compares the expected DOI with any metadata found in the downloaded data.
    3. Records the verification status.

    Returns:
        Dictionary with verification results:
        {
            "status": "pass" | "fail" | "version_mismatch",
            "expected_doi": str,
            "expected_url": str,
            "found_doi": Optional[str],
            "url_reachable": bool,
            "message": str
        }
    """
    result = {
        "status": "fail",
        "expected_doi": DATASET_DOI,
        "expected_url": DATASET_URL,
        "found_doi": None,
        "url_reachable": False,
        "message": ""
    }

    # Step 1: Check URL reachability
    logger.info(f"Checking URL reachability: {DATASET_URL}")
    reachable, error = check_url_reachable(DATASET_URL)
    result["url_reachable"] = reachable

    if not reachable:
        msg = f"Dataset URL is not reachable: {error}"
        logger.warning(msg)
        result["message"] = msg
        # Per task spec: log WARNING, record version_mismatch, continue (do NOT exit 1)
        result["status"] = "version_mismatch"
        return result

    logger.info("Dataset URL is reachable.")

    # Step 2: Look for metadata in downloaded data
    data_root = get_data_root()
    raw_data_dir = data_root / "raw"

    found_doi = None

    # Check for common metadata files
    metadata_files = [
        raw_data_dir / "metadata.json",
        raw_data_dir / "README.md",
        raw_data_dir / "dataset_info.json",
        raw_data_dir / "provenance.json"
    ]

    for meta_file in metadata_files:
        if meta_file.exists():
            logger.info(f"Checking metadata file: {meta_file}")
            try:
                if meta_file.suffix == '.json':
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                        # Look for DOI in common keys
                        for key in ['doi', 'DOI', 'dataset_doi', 'identifier']:
                            if key in meta_data and meta_data[key]:
                                found_doi = str(meta_data[key])
                                break
                elif meta_file.suffix in ['.md', '.txt']:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Simple heuristic: look for DOI pattern
                        if DATASET_DOI in content:
                            found_doi = DATASET_DOI
                            break
            except Exception as e:
                logger.warning(f"Could not parse metadata file {meta_file}: {e}")
                continue

            if found_doi:
                break

    result["found_doi"] = found_doi

    # Step 3: Compare DOIs
    if found_doi is None:
        # No metadata found to compare - this is a potential issue but not a hard failure
        # per task spec: if mismatch or URL unreachable, log WARNING and record version_mismatch
        msg = "No dataset metadata found to verify DOI. Cannot confirm provenance."
        logger.warning(msg)
        result["message"] = msg
        result["status"] = "version_mismatch"
        return result

    if found_doi == DATASET_DOI:
        result["status"] = "pass"
        result["message"] = f"Provenance verified: DOI matches ({DATASET_DOI})"
        logger.info(result["message"])
    else:
        msg = f"DOI mismatch: expected '{DATASET_DOI}', found '{found_doi}'"
        logger.warning(msg)
        result["message"] = msg
        result["status"] = "version_mismatch"

    return result


def save_provenance_result(result: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the provenance verification result to a JSON file.

    Args:
        result: The verification result dictionary.
        output_path: Optional custom output path. Defaults to state/provenance_check.json.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        state_root = get_state_root()
        ensure_directories(state_root)
        output_path = state_root / "provenance_check.json"

    write_json(result, output_path)
    logger.info(f"Provenance check result saved to {output_path}")
    return output_path


def main() -> int:
    """
    Main entry point for the provenance verification script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Setup logging
    setup_logging_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, setup_logging_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting provenance verification...")
    logger.info(f"Expected DOI: {DATASET_DOI}")
    logger.info(f"Expected URL: {DATASET_URL}")

    try:
        # Run verification
        result = verify_provenance()

        # Save result
        save_provenance_result(result)

        # Log final status
        logger.info(f"Verification status: {result['status']}")
        logger.info(f"Message: {result['message']}")

        # Per task spec: Do NOT exit with code 1 on mismatch, only log warning
        # Always exit 0 to allow pipeline to continue
        return 0

    except Exception as e:
        logger.error(f"Provenance verification failed with exception: {e}", exc_info=True)
        # Record failure but still exit 0 per task spec (log warning, continue)
        error_result = {
            "status": "fail",
            "expected_doi": DATASET_DOI,
            "expected_url": DATASET_URL,
            "found_doi": None,
            "url_reachable": False,
            "message": f"Exception during verification: {str(e)}"
        }
        try:
            save_provenance_result(error_result)
        except Exception as save_err:
            logger.error(f"Failed to save error result: {save_err}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
