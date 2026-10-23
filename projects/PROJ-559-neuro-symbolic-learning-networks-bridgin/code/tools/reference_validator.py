"""
Reference Validator

This script validates a set of external URLs against a title‑overlap
threshold. If any URL fails validation, the script logs an error and exits
with status 1, causing the CI pipeline to abort. On success it creates an
empty marker file at ``state/validation/citation_gate_passed.txt``.
"""

import sys
import re
import logging

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# List of external URLs that must be validated. These are the URLs mentioned
# in the project specification (ASSISTments dataset, Khan Academy dataset,
# and the BKT repository). Add additional URLs here if the project expands.
URLS_TO_VALIDATE = [
    "https://huggingface.co/datasets/assistments/2009-2010",
    "https://huggingface.co/datasets/khanacademy/math",
    "https://github.com/psouris/BKT",
]

# Title‑overlap threshold (as required by the Constitution)
TITLE_OVERLAP_THRESHOLD = 0.8

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)  # Uses the project‑wide logger configuration

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_title(url: str) -> str | None:
    """
    Retrieve the HTML title of the given URL.

    Returns ``None`` if the request fails or the title cannot be extracted.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        log.error(f"Failed to fetch URL {url}: {exc}")
        return None

    # Extract the <title> tag (case‑insensitive)
    match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE | re.DOTALL)
    if not match:
        log.error(f"Could not locate a <title> tag for URL {url}")
        return None

    title = match.group(1).strip()
    log.debug(f"Fetched title for {url!r}: {title!r}")
    return title

def compute_overlap(url: str, title: str) -> float:
    """
    Compute a simple token‑overlap ratio between the URL domain and the page title.

    The overlap is defined as:
        |tokens(url) ∩ tokens(title)| / |tokens(title)|
    where tokens are alphanumeric words converted to lower‑case.
    """
    # Tokenise the domain part of the URL (e.g. ``huggingface.co``)
    domain = re.sub(r"https?://", "", url).split("/")[0]
    url_tokens = set(re.findall(r"\w+", domain.lower()))

    # Tokenise the title
    title_tokens = set(re.findall(r"\w+", title.lower()))
    if not title_tokens:
        return 0.0

    overlap = len(url_tokens & title_tokens) / len(title_tokens)
    log.debug(f"Overlap for {url!r}: {overlap:.3f}")
    return overlap

# ----------------------------------------------------------------------
# Main validation routine
# ----------------------------------------------------------------------
def main() -> int:
    """
    Validate each URL in ``URLS_TO_VALIDATE``. On the first failure the script
    logs an error and returns a non‑zero exit code. If all URLs pass, an empty
    marker file is created to signal success to downstream CI steps.
    """
    for url in URLS_TO_VALIDATE:
        title = fetch_title(url)
        if title is None:
            log.error(f"ERROR: URL validation failed for {url}")
            return 1

        overlap = compute_overlap(url, title)
        if overlap < TITLE_OVERLAP_THRESHOLD:
            log.error(f"ERROR: URL validation failed for {url}")
            return 1

    # All URLs passed – create the empty marker file
    marker_path = paths.path("state", "validation", "citation_gate_passed.txt")
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()
    log.info("Citation‑gate validation succeeded; marker file created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
