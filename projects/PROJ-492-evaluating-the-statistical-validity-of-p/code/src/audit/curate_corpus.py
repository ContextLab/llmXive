"""
curate_corpus.py

Curate a deterministic corpus of ≥ 300 reachable URLs that point to public
A/B test summaries, download each page, store the raw HTML snapshot under
``data/raw/``, and generate ``data/checksums.txt`` containing SHA‑256 hashes
of all snapshots.

The script is deliberately self‑contained and uses only the Python standard
library together with the ``llmxive_toolkit`` helpers for path handling and
logging. No external dependencies are required.
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
# Seed index pages that list case‑study style A/B test summaries.
# These pages are publicly reachable and contain many links to individual
# summaries.  The list is deliberately small – the script discovers further
# URLs by parsing the index pages.
INDEX_PAGES = [
    "https://vwo.com/case-studies/",
    "https://www.optimizely.com/insights/case-studies/",
]

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
    """Download a page and return its HTML as text."""
    log.debug(f"Fetching URL: {url}")
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text

def _extract_candidate_urls(html: str) -> Set[str]:
    """
    Very‑lightweight extraction of ``href`` attributes that look like
    public A/B test summaries.

    The heuristic keeps URLs that:
    * start with ``http`` (absolute)
    * contain the substring ``case-studies`` or ``ab-test`` (case‑insensitive)
    """
    candidates: Set[str] = set()
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
        if not href.lower().startswith("http"):
            continue
        if re.search(r"case[-_]studies|ab[-_]test", href, re.IGNORECASE):
            candidates.add(href.rstrip("/"))
    return candidates

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
    1. Crawl the ``INDEX_PAGES`` for candidate summary URLs.
    2. Deduplicate, sort, and keep at least ``MIN_URLS`` entries.
    3. Write the final list to ``data/input/urls.csv``.
    4. Download each URL, store the raw HTML under ``data/raw/``.
    5. Compute SHA‑256 hashes and write ``data/checksums.txt``.
    """
    # ------------------------------------------------------------------- #
    # Step 1 – Gather candidate URLs
    # ------------------------------------------------------------------- #
    log.info("Collecting candidate URLs from index pages …")
    candidate_urls: Set[str] = set()
    for idx_url in INDEX_PAGES:
        try:
            html = _fetch_page(idx_url)
        except Exception as exc:
            log.error(f"Failed to fetch index page {idx_url}: {exc}")
            continue
        found = _extract_candidate_urls(html)
        log.debug(f"Found {len(found)} candidates on {idx_url}")
        candidate_urls.update(found)

    if len(candidate_urls) < MIN_URLS:
        log.error(
            f"Only {len(candidate_urls)} candidate URLs collected – "
            f"need at least {MIN_URLS}. Abort."
        )
        return 1

    # ------------------------------------------------------------------- #
    # Step 2 – Deterministic selection
    # ------------------------------------------------------------------- #
    selected_urls: List[str] = sorted(candidate_urls)[:MIN_URLS]
    log.info(f"Selected {len(selected_urls)} URLs for the corpus.")

    # ------------------------------------------------------------------- #
    # Step 3 – Write urls.csv
    # ------------------------------------------------------------------- #
    urls_csv_path = paths.data("input", "urls.csv")
    with urls_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])
        for u in selected_urls:
            writer.writerow([u])
    log.info(f"Wrote URL list to {urls_csv_path}")

    # ------------------------------------------------------------------- #
    # Step 4 – Download raw HTML snapshots
    # ------------------------------------------------------------------- #
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    snapshot_paths: List[Path] = []
    for u in selected_urls:
        try:
            snap_path = _download_and_save(u, raw_dir)
            snapshot_paths.append(snap_path)
        except Exception as exc:
            log.error(f"Failed to download {u}: {exc}")
            # According to the specification, a failure must abort the run.
            return 1

    # ------------------------------------------------------------------- #
    # Step 5 – Compute checksums
    # ------------------------------------------------------------------- #
    checksums_path = paths.data("checksums.txt")
    with checksums_path.open("w", encoding="utf-8") as f:
        for p in snapshot_paths:
            digest = _compute_sha256(p)
            # Store the path relative to the project root, matching the
            # conventional format of ``sha256sum`` output.
            rel_path = p.relative_to(paths.root)
            f.write(f"{digest}  {rel_path}\n")
    log.info(f"Wrote SHA‑256 checksums to {checksums_path}")

    log.info("Corpus curation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
