"""
curate_corpus.py

Curate a deterministic corpus of ≥ 300 reachable URLs that point to public
A/B test summaries, download each page, store the raw HTML snapshot under
``data/raw/``, and generate ``data/checksums.txt`` containing SHA‑256 hashes
of all snapshots.

The script now reads the pre‑populated ``data/input/urls.csv`` (which already
contains a large list of candidate URLs), selects the first 300 URLs that can
be successfully fetched, writes the deterministic list back to the same CSV,
stores each HTML snapshot under ``data/raw/`` and finally writes a checksum
file. All operations are deterministic (sorted URLs, fixed seed) and abort
with a non‑zero exit code if fewer than 300 reachable URLs are obtained.
"""

import csv
import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import List, Set

import requests
from llmxive_toolkit import paths, get_logger

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
# Minimum number of URLs required for the corpus.
MIN_URLS = 300

# HTTP request settings.
REQUEST_TIMEOUT = 15  # seconds
USER_AGENT = (
    "Mozilla/5.0 (compatible; llmxive‑audit/1.0; +https://github.com/llmxive)"
)
HEADERS = {"User-Agent": USER_AGENT}

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
log = get_logger(__name__)

def _fetch_page(url: str) -> str:
    """Download a page and return its HTML as UTF‑8 text.

    The response is decoded using UTF‑8 with ``replace`` error handling to
    avoid codec errors on pages that incorrectly declare their encoding.
    """
    log.debug(f"Fetching URL: {url}")
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, stream=True)
    response.raise_for_status()
    # Force UTF‑8 decoding, replace undecodable bytes.
    return response.content.decode("utf-8", errors="replace")

def _sanitize_filename(url: str) -> str:
    """
    Convert a URL into a safe filename for the raw HTML snapshot.
    Example:
        https://vwo.com/case-studies/brand-x/  ->  vwo.com_case-studies_brand-x.html
    """
    # Remove scheme
    stripped = re.sub(r"^https?://", "", url)
    # Replace any non‑alphanumeric character with an underscore
    sanitized = re.sub(r"[^0-9a-zA-Z]+", "_", stripped)
    # Truncate to a reasonable length to avoid filesystem limits
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return f"{sanitized}.html"

def _download_and_save(url: str, dest_dir: Path) -> Path:
    """Download ``url`` and write the HTML to ``dest_dir`` using a safe name."""
    html = _fetch_page(url)
    filename = _sanitize_filename(url)
    out_path = dest_dir / filename
    out_path.write_text(html, encoding="utf-8")
    log.info(f"Saved HTML for {url} → {out_path}")
    return out_path

def _compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main() -> int:
    """
    1. Load candidate URLs from the existing ``data/input/urls.csv``.
    2. Deterministically select (sorted) URLs and attempt to download them
       until at least ``MIN_URLS`` successful snapshots are obtained.
    3. Overwrite ``data/input/urls.csv`` with the final deterministic list.
    4. Store raw HTML snapshots under ``data/raw/``.
    5. Compute SHA‑256 hashes and write ``data/checksums.txt``.
    """
    # ------------------------------------------------------------------- #
    # Step 1 – Load candidate URLs
    # ------------------------------------------------------------------- #
    input_csv_path = paths.data("input", "urls.csv")
    if not input_csv_path.exists():
        log.error(f"Input CSV not found: {input_csv_path}")
        return 1

    with input_csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        candidate_urls: List[str] = [row["url"].strip() for row in reader if row.get("url")]

    if not candidate_urls:
        log.error("No URLs found in the input CSV.")
        return 1

    # Ensure deterministic order
    candidate_urls = sorted(set(candidate_urls))

    # ------------------------------------------------------------------- #
    # Step 2 – Download until we have MIN_URLS successful snapshots
    # ------------------------------------------------------------------- #
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    successful_urls: List[str] = []
    snapshot_paths: List[Path] = []

    for url in candidate_urls:
        if len(successful_urls) >= MIN_URLS:
            break
        try:
            snap_path = _download_and_save(url, raw_dir)
            successful_urls.append(url)
            snapshot_paths.append(snap_path)
        except Exception as exc:
            log.error(f"Failed to download {url}: {exc}")
            # Continue to next URL; we need MIN_URLS successful ones.
            continue

    if len(successful_urls) < MIN_URLS:
        log.error(
            f"Only {len(successful_urls)} URLs were successfully downloaded; "
            f"need at least {MIN_URLS}. Abort."
        )
        return 1

    # ------------------------------------------------------------------- #
    # Step 3 – Write deterministic urls.csv (the successful set)
    # ------------------------------------------------------------------- #
    urls_csv_path = paths.data("input", "urls.csv")
    with urls_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])
        for u in successful_urls:
            writer.writerow([u])
    log.info(f"Wrote {len(successful_urls)} URLs to {urls_csv_path}")

    # ------------------------------------------------------------------- #
    # Step 4 – Compute checksums
    # ------------------------------------------------------------------- #
    checksums_path = paths.data("checksums.txt")
    with checksums_path.open("w", encoding="utf-8") as f:
        for p in snapshot_paths:
            digest = _compute_sha256(p)
            rel_path = p.relative_to(paths.root)
            f.write(f"{digest}  {rel_path}\\n")
    log.info(f"Wrote SHA‑256 checksums to {checksums_path}")

    log.info("Corpus curation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
