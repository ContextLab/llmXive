"""
arXiv ID verification module (T013-VALIDATE-IDS).

Verifies that the arXiv IDs referenced by this project
(arXiv:2106.08611 and arXiv:2305.06325) exist and are accessible
via the public arXiv export API, using native HTTP requests only.
No external CLI agents are invoked.
"""
import sys
import xml.etree.ElementTree as ET

import requests

from config import get_logger

logger = get_logger(__name__)

ARXIV_API_BASE = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"

def _fetch_entries(arxiv_id: str, timeout: int):
    """Fetch the Atom feed entries for a single arXiv ID."""
    clean_id = arxiv_id.replace("arXiv:", "").strip()
    if not clean_id:
        raise RuntimeError(f"Invalid arXiv ID format: {arxiv_id!r}")

    params = {"id_list": clean_id, "max_results": 1}
    try:
        response = requests.get(ARXIV_API_BASE, params=params, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Source unreachable: failed to contact arXiv API for ID {clean_id}: {e}"
        ) from e

    if response.status_code != 200:
        raise RuntimeError(
            f"arXiv API returned HTTP {response.status_code} for ID {clean_id}"
        )

    # Parse the Atom XML feed to confirm the entry genuinely exists.
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as e:
        raise RuntimeError(
            f"arXiv API returned malformed XML for ID {clean_id}: {e}"
        ) from e

    entries = root.findall(f"{ATOM_NS}entry")
    return clean_id, entries

def validate_arxiv_id(arxiv_id: str, timeout: int = 10) -> bool:
    """
    Verify that an arXiv ID exists and returns a valid response.

    Args:
        arxiv_id: The arXiv ID string (e.g., '2106.08611' or 'arXiv:2106.08611').
        timeout: Request timeout in seconds.

    Returns:
        True if the ID is valid and accessible.

    Raises:
        RuntimeError: If the ID is invalid or the source is unreachable.
    """
    clean_id, entries = _fetch_entries(arxiv_id, timeout)

    if not entries:
        raise RuntimeError(
            f"arXiv ID {clean_id} not found in database (API returned no entries)."
        )

    entry = entries[0]
    entry_id_el = entry.find(f"{ATOM_NS}id")
    title_el = entry.find(f"{ATOM_NS}title")
    if entry_id_el is None or not (entry_id_el.text or "").strip():
        raise RuntimeError(
            f"arXiv ID {clean_id} returned an entry without an identifier."
        )

    # The API echoes the canonical abs URL, e.g.
    # http://arxiv.org/abs/2106.08611v1
    if clean_id not in entry_id_el.text:
        raise RuntimeError(
            f"arXiv ID mismatch: requested {clean_id}, API returned "
            f"{entry_id_el.text}"
        )

    title = (title_el.text or "").strip() if title_el is not None else ""
    logger.info(
        f"arXiv ID {clean_id} validated successfully (title: {title!r})."
    )
    return True

def validate_required_ids(timeout: int = 10) -> dict:
    """
    Validate all arXiv IDs required by this project.

    Returns:
        Dict mapping each arXiv ID to True on success.

    Raises:
        RuntimeError: If any required ID is invalid or unreachable.
    """
    required_ids = ["2106.08611", "2305.06325"]
    results = {}
    for aid in required_ids:
        results[aid] = validate_arxiv_id(aid, timeout=timeout)
    return results

def main():
    """CLI entry point for validation."""
    logger.info("Starting arXiv ID validation...")
    try:
        results = validate_required_ids()
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    for aid, ok in results.items():
        logger.info(f"  [{'OK' if ok else 'FAIL'}] arXiv:{aid}")
    logger.info("All required arXiv IDs validated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
