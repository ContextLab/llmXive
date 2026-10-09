import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import requests
import yaml

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Hard‑coded whitelist – only allowed domains for citations.
# NOTE: An empty string must NOT be present in this list (per task spec).
WHITELIST: List[str] = [
    "https://materialsproject.org",
]


def _extract_urls_from_metadata(metadata_path: str) -> List[str]:
    """
    Load the metadata YAML file and pull out any URLs it contains.

    The project’s ``metadata.yaml`` currently stores URLs under a top‑level
    ``sources`` list where each entry is a mapping that may include a ``url``
    key.  This helper is tolerant of minor schema variations – it will also
    look for a top‑level ``urls`` key or a ``citation`` key if present.

    Parameters
    ----------
    metadata_path: str
        Path to the ``metadata.yaml`` file.

    Returns
    -------
    List[str]
        All discovered URL strings (may be empty).
    """
    if not os.path.exists(metadata_path):
        logger.debug(f"Metadata file not found at {metadata_path}. No URLs extracted.")
        return []

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.error(f"Failed to parse metadata file '{metadata_path}': {exc}")
        raise

    urls: List[str] = []

    # Common patterns
    if isinstance(data, dict):
        # 1. ``sources`` is a list of dicts with a ``url`` field
        sources = data.get("sources")
        if isinstance(sources, list):
            for entry in sources:
                if isinstance(entry, dict):
                    url = entry.get("url")
                    if isinstance(url, str):
                        urls.append(url)

        # 2. Direct ``urls`` list
        if "urls" in data and isinstance(data["urls"], list):
            urls.extend([u for u in data["urls"] if isinstance(u, str)])

        # 3. Single ``citation`` string
        citation = data.get("citation")
        if isinstance(citation, str):
            urls.append(citation)

    # Filter out empty strings that may have slipped in
    urls = [u for u in urls if u.strip()]
    logger.debug(f"Extracted URLs from metadata: {urls}")
    return urls


def _is_url_whitelisted(url: str) -> bool:
    """
    Determine whether a URL belongs to an allowed domain.

    The check is performed via ``str.startswith`` against each entry in
    ``WHITELIST``.  Exact matches are also accepted.

    Parameters
    ----------
    url: str

    Returns
    -------
    bool
    """
    return any(url.startswith(allowed) for allowed in WHITELIST)


def _check_url_reachable(url: str) -> bool:
    """
    Perform a simple HTTP GET request to confirm the URL returns status 200.

    A short timeout is used to avoid hanging the pipeline.  Redirection
    (3xx) is followed automatically by ``requests``; any non‑200 response
    is treated as a failure.

    Parameters
    ----------
    url: str

    Returns
    -------
    bool
        ``True`` if the request succeeded with status 200, else ``False``.
    """
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException as exc:
        logger.warning(f"Request to '{url}' failed: {exc}")
        return False


def validate_citations(url: str, metadata_path: str) -> dict:
    """
    Validate citation URLs against a whitelist and confirm they are reachable.

    The function follows the exact contract required by task **T004c**:
    * Parse ``metadata_path`` (``projects/…/data/metadata.yaml``) and collect
      any URLs it contains.
    * If no URLs are found in the metadata, fall back to the ``url`` argument
      supplied to the function.
    * Each discovered URL must:
        - Start with one of the whitelisted prefixes.
        - Respond to an HTTP GET request with status code 200.
    * Return a dictionary describing the validation outcome.

    Parameters
    ----------
    url: str
        Primary URL to validate (used when the metadata file does not list any).
    metadata_path: str
        Path to the metadata YAML file.

    Returns
    -------
    dict
        ``{"success": True, "error_code": None, "message": "OK"}`` on success,
        otherwise ``{"success": False, "error_code": "URL_INVALID",
        "message": "URL not in whitelist or unreachable"}``.
    """
    # Step 1: Extract URLs from the metadata file
    try:
        candidate_urls = _extract_urls_from_metadata(metadata_path)
    except Exception as exc:
        # Parsing error – treat as failure per spec
        return {
            "success": False,
            "error_code": "METADATA_PARSE_ERROR",
            "message": str(exc),
        }

    # If metadata yielded no URLs, use the supplied ``url`` argument
    if not candidate_urls:
        if url:
            candidate_urls = [url]
        else:
            return {
                "success": False,
                "error_code": "NO_URLS_FOUND",
                "message": "No URLs found in metadata and no URL argument provided.",
            }

    # Validate each URL against whitelist and reachability.
    # The spec requires a single generic error message for any failure.
    for candidate in candidate_urls:
        if not _is_url_whitelisted(candidate):
            return {
                "success": False,
                "error_code": "URL_INVALID",
                "message": "URL not in whitelist or unreachable",
            }
        if not _check_url_reachable(candidate):
            return {
                "success": False,
                "error_code": "URL_INVALID",
                "message": "URL not in whitelist or unreachable",
            }

    # All URLs passed validation
    return {"success": True, "error_code": None, "message": "OK"}