"""
Curate a deterministic corpus of public A/B‑test summary URLs.

This script reads ``data/input/urls.csv`` (a CSV with a header ``url``),
downloads each URL, stores the raw HTML snapshot under ``data/raw/`` using
a deterministic, filesystem‑safe filename, and writes a SHA‑256 checksum
for every snapshot to ``data/checksums.txt``.

The implementation follows the contract described in the project API
surface (see ``code/src/audit/curate_corpus.py``) and satisfies the
verification requirements for task **T017**:
  * ``urls.csv`` contains ≥ 300 rows,
  * a raw HTML file exists for every URL,
  * ``data/checksums.txt`` lists a hash line for each snapshot,
  * all downloads return HTTP 200 and HTML content.
"""
import csv
import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import List

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions (public API as required by the spec)
# ----------------------------------------------------------------------
def _load_candidate_urls(csv_path: Path) -> List[str]:
    """
    Read the ``url`` column from the input CSV and return a list of URLs.

    Parameters
    ----------
    csv_path: Path
        Path to ``data/input/urls.csv``.

    Returns
    -------
    List[str]
        List of URLs in the order they appear in the CSV (duplicates are
        preserved – deduplication is performed later in ``main``).
    """
    if not csv_path.is_file():
        logger.error(f"ERR-001: Input CSV not found at {csv_path}")
        raise FileNotFoundError(f"Input CSV not found at {csv_path}")

    urls: List[str] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "url" not in reader.fieldnames:
            logger.error("ERR-002: CSV missing required 'url' header")
            raise ValueError("CSV missing required 'url' header")
        for row in reader:
            url = row["url"].strip()
            if url:
                urls.append(url)
    return urls

def _sanitize_url(url: str) -> str:
    """
    Produce a deterministic, filesystem‑safe filename for a URL.

    The function:
      * lower‑cases the URL,
      * removes the protocol (``http://`` or ``https://``),
      * replaces any character that is not alphanumeric, ``-`` or ``_``
        with an underscore,
      * collapses consecutive underscores,
      * truncates the result to 200 characters (more than enough for
        uniqueness in this corpus).

    The returned string does **not** include a file extension.
    """
    # Strip protocol
    url_no_proto = re.sub(r"^https?://", "", url.lower())
    # Replace non‑safe characters with underscore
    safe = re.sub(r"[^a-z0-9_-]+", "_", url_no_proto)
    # Collapse multiple underscores
    safe = re.sub(r"_+", "_", safe).strip("_")
    # Truncate to avoid extremely long filenames
    return safe[:200]

def _download_page(url: str) -> bytes:
    """
    Download a page and return its raw ``bytes`` content.

    Raises
    ------
    requests.RequestException
        For network‑level errors or non‑200 responses.
    ValueError
        If the ``Content‑Type`` header does not indicate HTML.
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "ab-audit-bot/1.0"})
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error(f"ERR-003: Failed to fetch {url} – {exc}")
        raise

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.lower():
        logger.error(f"ERR-004: URL {url} returned non‑HTML content type '{content_type}'")
        raise ValueError(f"Non‑HTML content at {url}")

    return response.content

def _write_snapshot(content: bytes, dest_path: Path) -> None:
    """
    Write raw HTML bytes to ``dest_path``.  The parent directory is created
    if it does not already exist.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(content)

def _compute_sha256(file_path: Path) -> str:
    """
    Return the SHA‑256 hexadecimal digest of the file at ``file_path``.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for the corpus curation script.

    Workflow
    ---------
    1. Load URLs from ``data/input/urls.csv``.
    2. Ensure at least 300 distinct URLs are present.
    3. Deduplicate while preserving deterministic order.
    4. For each URL:
         a. Download the page (must return HTTP 200 and HTML).
         b. Write the snapshot to ``data/raw/<sanitized>.html``.
         c. Compute the SHA‑256 checksum.
    5. Write all checksum lines to ``data/checksums.txt`` in the format
       ``<hash>  <filename>`` (two spaces as in typical ``sha256sum`` output).

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    # Paths derived via llmxive_toolkit for reproducibility
    input_csv = paths.data("input", "urls.csv")
    raw_dir = paths.data("raw")
    checksums_path = paths.data("checksums.txt")

    logger.info(f"Loading candidate URLs from {input_csv}")
    try:
        candidate_urls = _load_candidate_urls(input_csv)
    except Exception:
        return 1

    # Deduplicate while preserving order
    seen = set()
    urls: List[str] = []
    for u in candidate_urls:
        if u not in seen:
            seen.add(u)
            urls.append(u)

    if len(urls) < 300:
        logger.error(f"ERR-005: Corpus contains only {len(urls)} URLs; at least 300 required.")
        return 1

    logger.info(f"Curating corpus of {len(urls)} distinct URLs")
    raw_dir.mkdir(parents=True, exist_ok=True)

    checksum_lines: List[str] = []

    for idx, url in enumerate(urls, start=1):
        logger.info(f"[{idx}/{len(urls)}] Processing {url}")
        try:
            content = _download_page(url)
        except Exception:
            # Propagate the error – a dead link violates the verification
            logger.error(f"ERR-006: Unable to download {url}")
            return 1

        filename = f"{_sanitize_url(url)}.html"
        dest_path = raw_dir / filename

        try:
            _write_snapshot(content, dest_path)
        except Exception as exc:
            logger.error(f"ERR-007: Failed to write snapshot for {url} – {exc}")
            return 1

        try:
            file_hash = _compute_sha256(dest_path)
        except Exception as exc:
            logger.error(f"ERR-008: Failed to compute SHA‑256 for {dest_path} – {exc}")
            return 1

        checksum_lines.append(f"{file_hash}  {filename}")

    # Write checksums file
    try:
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        with checksums_path.open("w", encoding="utf-8") as f:
            for line in checksum_lines:
                f.write(line + "\n")
    except Exception as exc:
        logger.error(f"ERR-009: Unable to write checksums file – {exc}")
        return 1

    logger.info(f"Corpus curation complete. Snapshots stored in {raw_dir}")
    logger.info(f"Checksums written to {checksums_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())