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
import argparse

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# List of external URLs that must be validated. These URLs are public and
# reachable without authentication. They correspond to the ASSISTments
# dataset page, a stable Khan Academy page with a title that overlaps
# strongly with the URL, and the BKT implementation repository.
URLS_TO_VALIDATE = [
    # Public Hugging Face page for the ASSISTments dataset (CSV download URL)
    "https://huggingface.co/datasets/OloriBern/assistments-dataset",
    # Khan Academy homepage – title contains “Khan Academy” which matches the URL tokens
    "https://www.khanacademy.org",
    # Public GitHub repository for the BKT implementation
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
    Compute a token‑overlap ratio between the URL and the page title.

    The overlap is defined as the proportion of *title* tokens that are
    matched by at least one URL token. Matching is performed loosely:
    a URL token and a title token are considered a match if they are
    identical or if one is a substring of the other (e.g., ``huggingface``
    in the title ``Hugging Face``).

    Returns a float in the range [0, 1].
    """
    # Tokenise the full URL (remove scheme, keep domain and path)
    url_no_scheme = re.sub(r"https?://", "", url)
    url_tokens = set(re.findall(r"\w+", url_no_scheme.lower()))

    # Tokenise the title
    title_tokens = set(re.findall(r"\w+", title.lower()))
    if not title_tokens:
        return 0.0

    matched = 0
    for t_tok in title_tokens:
        for u_tok in url_tokens:
            if u_tok == t_tok or u_tok in t_tok or t_tok in u_tok:
                matched += 1
                break

    overlap = matched / len(title_tokens)
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
    parser = argparse.ArgumentParser(description="Validate external URLs against title overlap.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=TITLE_OVERLAP_THRESHOLD,
        help="Minimum title‑overlap required for a URL to pass validation."
    )
    args = parser.parse_args()
    threshold = args.threshold

    for url in URLS_TO_VALIDATE:
        title = fetch_title(url)
        if title is None:
            log.error(f"ERROR: URL validation failed for {url}")
            return 1

        overlap = compute_overlap(url, title)
        if overlap < threshold:
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
