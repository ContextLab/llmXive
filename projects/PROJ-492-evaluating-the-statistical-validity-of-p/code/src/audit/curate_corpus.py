"""
Curate a deterministic corpus of public A/B test summary URLs.

This script reads the candidate URL list from ``data/input/urls.csv``,
ensures at least 300 distinct, reachable URLs, downloads each page,
stores the raw HTML snapshot under ``data/raw/`` using a deterministic,
filesystem‑safe filename derived from the URL, and writes SHA‑256 checksums
for every snapshot to ``data/checksums.txt`` (two‑space format, like
``sha256sum``).

The implementation follows the API surface defined in the project:
* ``paths`` from ``llmxive_toolkit`` for all filesystem locations.
* ``get_logger`` for structured logging.
* All network errors raise exceptions – no silent fall‑backs – to satisfy
  the “real data only” constraint.
"""

import csv
import hashlib
import logging
from pathlib import Path
from typing import List

import requests

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Helper functions (mirroring the originally‑documented API)
# ----------------------------------------------------------------------
def _load_candidate_urls(csv_path: Path) -> List[str]:
    """
    Read the ``url`` column from the input CSV and return a list of URLs.
    Duplicates are preserved here – deduplication is performed later while
    preserving the original order.
    """
    urls = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            if url:
                urls.append(url)
    return urls

def _sanitize_url(url: str) -> str:
    """
    Produce a deterministic, filesystem‑safe filename for a URL.

    The algorithm matches the description in ``curate_corpus.py``:
    * lower‑case
    * strip ``http://`` or ``https://``
    * replace any character that is not alphanumeric, ``-`` or ``_`` with
      an underscore
    * collapse consecutive underscores
    * truncate to 200 characters
    * do **not** add a file extension
    """
    url = url.lower()
    if url.startswith("http://"):
        url = url[7:]
    elif url.startswith("https://"):
        url = url[8:]

    # Replace disallowed characters with underscore
    safe = []
    for ch in url:
        if ch.isalnum() or ch in "-_":
            safe.append(ch)
        else:
            safe.append("_")
    sanitized = "".join(safe)

    # Collapse consecutive underscores
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")

    # Truncate
    return sanitized[:200]

def _download_page(url: str) -> bytes:
    """
    Download a page and return its raw ``bytes`` content.

    Raises:
        requests.RequestException – for network‑level errors.
        ValueError – if the ``Content‑Type`` header does not indicate HTML.
    """
    response = requests.get(url, timeout=30)
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Unexpected HTTP status {response.status_code} for {url}"
        )
    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.lower():
        raise ValueError(f"URL did not return HTML content: {url}")
    return response.content

def _write_snapshot(content: bytes, dest_path: Path) -> None:
    """
    Write raw HTML bytes to ``dest_path``.  Parent directories are created
    automatically.
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
    Entry point for corpus curation.

    Workflow:
    1. Load candidate URLs from ``data/input/urls.csv``.
    2. Ensure at least 300 distinct URLs (deduplicated while preserving order).
    3. For each URL:
         a. Sanitize to a deterministic filename.
         b. Download the page (must return HTTP 200 and HTML).
         c. Write the snapshot to ``data/raw/<sanitized>.html``.
         d. Compute its SHA‑256 checksum.
    4. Write all checksum lines to ``data/checksums.txt`` using the
       ``<hash>  <filename>`` format.
    """
    logger = get_logger(__name__)

    # 1. Load candidate URLs
    input_csv = paths.data("input", "urls.csv")
    logger.info(f"Loading candidate URLs from {input_csv}")
    if not input_csv.is_file():
        logger.error(f"Input CSV not found: {input_csv}")
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    candidate_urls = _load_candidate_urls(input_csv)
    logger.info(f"Found {len(candidate_urls)} URLs in the input file")

    # 2. Deduplicate while preserving order
    seen = set()
    distinct_urls = []
    for url in candidate_urls:
        if url not in seen:
            seen.add(url)
            distinct_urls.append(url)

    logger.info(f"Deduplicated to {len(distinct_urls)} distinct URLs")

    if len(distinct_urls) < 300:
        error_msg = (
            f"Corpus must contain at least 300 distinct URLs; only "
            f"{len(distinct_urls)} were found."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Limit to the first 300 URLs to keep runtime bounded
    urls_to_process = distinct_urls[:300]

    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    checksum_lines: List[str] = []

    for idx, url in enumerate(urls_to_process, start=1):
        logger.info(f"[{idx}/{len(urls_to_process)}] Processing {url}")

        # a. Sanitize filename
        filename_base = _sanitize_url(url)
        snapshot_path = raw_dir / f"{filename_base}.html"

        # b. Download page
        content = _download_page(url)

        # c. Write snapshot
        _write_snapshot(content, snapshot_path)

        # d. Compute checksum
        file_hash = _compute_sha256(snapshot_path)
        # Two spaces as per typical sha256sum output
        checksum_line = f"{file_hash}  {snapshot_path.name}"
        checksum_lines.append(checksum_line)

    # 4. Write checksums file
    checksums_path = paths.data("checksums.txt")
    logger.info(f"Writing checksums for {len(checksum_lines)} files to {checksums_path}")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8", newline="\n") as f:
        for line in checksum_lines:
            f.write(line + "\n")

    logger.info("Corpus curation completed successfully.")
    return 0

if __name__ == "__main__":
    # When executed as a script, exit with the return code from ``main``.
    raise SystemExit(main())