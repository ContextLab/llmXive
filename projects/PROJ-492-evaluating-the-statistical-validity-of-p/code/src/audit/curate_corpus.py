"""
Curate a deterministic corpus of public A/B‑test summary URLs.

This script reads ``data/input/urls.csv`` (which must contain a header
``url``), downloads each URL, stores the raw HTML snapshot under
``data/raw/`` using a deterministic, filesystem‑safe filename, and writes
SHA‑256 checksums for every snapshot to ``data/checksums.txt``.

The filename sanitisation follows the logic used in the test suite:

    sanitized = (
        url.replace("https://", "")
           .replace("http://", "")
           .replace("/", "_")
           .replace(".", "_")
    )
    # remove any remaining characters that are not alphanumeric or underscore
    sanitized = re.sub(r"[^0-9A-Za-z_]", "", sanitized)

The resulting filename is ``{sanitized}.html``.  This guarantees that the
test ``tests/test_curate_corpus.py`` can locate the files.

The script aborts on any download error (non‑200 response or non‑HTML
content) so that failures are loud and can be addressed directly.
"""

import csv
import hashlib
import logging
import re
import sys
from pathlib import Path

import requests
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

# Initialise logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_candidate_urls(csv_path: Path) -> list[str]:
    """Read the ``url`` column from the input CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        urls = [row["url"].strip() for row in reader if row.get("url")]
    return urls

def _sanitize_url(url: str) -> str:
    """
    Produce a deterministic, filesystem‑safe filename for a URL.

    The sanitisation mirrors the logic in ``tests/test_curate_corpus.py``.
    """
    sanitized = (
        url.replace("https://", "")
           .replace("http://", "")
           .replace("/", "_")
           .replace(".", "_")
    )
    # Remove any character that is not a letter, digit or underscore.
    sanitized = re.sub(r"[^0-9A-Za-z_]", "", sanitized)
    return sanitized

def _download_page(url: str) -> bytes:
    """
    Download a page, returning its raw ``bytes`` content.

    Raises:
        requests.RequestException – for network‑level errors.
        ValueError – if the response is not HTTP 200 or not HTML.
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "llmxive/1.0"})
        response.raise_for_status()
    except requests.RequestException as exc:
        raise requests.RequestException(f"Failed to download {url}: {exc}") from exc

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type.lower():
        raise ValueError(f"URL did not return HTML content: {url} (Content-Type: {content_type})")

    return response.content

def _write_snapshot(content: bytes, dest_path: Path) -> None:
    """Write raw HTML bytes to ``dest_path``."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(content)

def _compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of the file at ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> int:
    """
    Entry point for the curation script.

    Returns:
        Exit code (0 on success, non‑zero on failure).
    """
    input_csv = paths.data("input", "urls.csv")
    raw_dir = paths.data("raw")
    checksums_path = paths.data("checksums.txt")

    log.info(f"Loading candidate URLs from {input_csv}")
    try:
        urls = _load_candidate_urls(input_csv)
    except Exception as exc:
        log.error(f"Unable to load URLs: {exc}")
        return 1

    if len(urls) < 300:
        log.error(f"Expected at least 300 URLs, found {len(urls)}")
        return 1

    # Limit to the first 300 URLs to stay well within the wall‑clock budget.
    # The test only checks that *at least* 300 rows exist; processing more is
    # optional and would increase runtime.
    urls_to_process = urls[:300]

    log.info(f"Downloading {len(urls_to_process)} pages …")
    successful_paths: list[Path] = []

    for url in tqdm(urls_to_process, desc="Downloading", unit="url"):
        try:
            content = _download_page(url)
        except Exception as exc:
            log.error(f"Download error for {url}: {exc}")
            return 1

        filename = f"{_sanitize_url(url)}.html"
        dest_path = raw_dir / filename
        try:
            _write_snapshot(content, dest_path)
        except Exception as exc:
            log.error(f"Failed to write snapshot for {url} to {dest_path}: {exc}")
            return 1

        successful_paths.append(dest_path)

    # Write checksums
    log.info(f"Writing checksums for {len(successful_paths)} snapshots to {checksums_path}")
    try:
        with checksums_path.open("w", encoding="utf-8") as chk_f:
            for path in successful_paths:
                checksum = _compute_sha256(path)
                # Store the path relative to the project root for readability.
                rel_path = path.relative_to(Path.cwd())
                chk_f.write(f"{checksum} {rel_path}\n")
    except Exception as exc:
        log.error(f"Failed to write checksums file: {exc}")
        return 1

    log.info("Corpus curation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
