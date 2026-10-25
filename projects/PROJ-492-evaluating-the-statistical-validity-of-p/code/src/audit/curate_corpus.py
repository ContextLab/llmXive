"""
curate_corpus.py

Script to create a deterministic corpus of ≥ 300 reachable URLs that
point to public A/B test summaries. The script performs the following
steps:

1. Retrieves a sitemap that lists many case‑study URLs from Optimizely
   (https://www.optimizely.com/sitemap.xml). The sitemap is publicly
   available and contains a large number of URLs.
2. Filters the URLs to keep only those that appear to be case‑study or
   blog‑post pages (heuristic: contain “case-study” or “blog” in the
   path). The filtered list is sorted to guarantee determinism.
3. Takes the first 300 URLs, downloads each page, and writes the raw HTML
   to ``data/raw/<sanitized_name>.html``.
4. Writes the list of URLs to ``data/input/urls.csv`` (header ``url``).
5. Computes a SHA‑256 checksum for every downloaded HTML file and writes
   the results to ``data/checksums.txt`` (format: ``<hash>  <relative_path>``).

The script is idempotent: if the output files already exist it will
skip re‑downloading the corresponding pages. All paths are built using
the ``llmxive_toolkit.paths`` helpers so they live inside the project
directory.

The script can be executed directly:

    python -m code.src.audit.curate_corpus

It exits with status 0 on success or propagates any exception (e.g.
network errors) to make failures loud.
"""
import csv
import hashlib
import logging
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

import requests
import xml.etree.ElementTree as ET

from llmxive_toolkit import paths, get_logger

# Configure a module‑level logger
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
SITEMAP_URL = "https://www.optimizely.com/sitemap.xml"
TARGET_COUNT = 300
MAX_WORKERS = 10
TIMEOUT = 20  # seconds per HTTP request

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sanitize_filename(url: str) -> str:
    """
    Convert a URL into a safe filename for storing the HTML snapshot.
    Only alphanumerics and underscores are kept.
    """
    # Remove scheme and replace non‑alphanumerics with underscores
    path = re.sub(r"^https?://", "", url)
    path = re.sub(r"[^A-Za-z0-9]+", "_", path)
    # Truncate to a reasonable length
    return path[:200] + ".html"

def _fetch_sitemap() -> List[str]:
    """
    Download the sitemap XML and return a list of URLs contained within.
    This implementation is robust to the presence or absence of XML
    namespaces.
    """
    log.info(f"Fetching sitemap from {SITEMAP_URL}")
    resp = requests.get(SITEMAP_URL, timeout=TIMEOUT)
    resp.raise_for_status()
    # Parse XML; use ``.//{*}url`` to match any namespace
    root = ET.fromstring(resp.content)

    urls: List[str] = []
    for url_elem in root.findall(".//{*}url"):
        loc = url_elem.find("{*}loc")
        if loc is not None and loc.text:
            urls.append(loc.text.strip())
    log.info(f"Found {len(urls)} URLs in sitemap")
    return urls

def _filter_candidate_urls(urls: List[str]) -> List[str]:
    """
    Keep URLs that plausibly point to A/B‑test case studies.
    Simple heuristic based on path keywords.
    """
    candidates = [
        u for u in urls
        if ("case-study" in u.lower() or "blog" in u.lower())
    ]
    log.info(f"Filtered down to {len(candidates)} candidate case‑study URLs")
    return sorted(set(candidates))

def _download_html(url: str, dest_path: Path) -> None:
    """
    Download a single URL and write its raw HTML to ``dest_path``.
    If the file already exists, the download is skipped.
    """
    if dest_path.exists():
        log.debug(f"File already exists, skipping download: {dest_path}")
        return

    log.debug(f"Downloading {url}")
    resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "ab-audit-bot/1.0"})
    resp.raise_for_status()

    # Ensure we got HTML (content‑type may include charset)
    content_type = resp.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        raise ValueError(f"URL did not return HTML: {url} (Content‑Type: {content_type})")

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_bytes(resp.content)
    log.debug(f"Wrote HTML to {dest_path}")

def _compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file's contents.
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
    Entry point for the script. Returns an exit code compatible with
    ``python -m`` execution.
    """
    try:
        # 1. Load sitemap and pick candidate URLs
        all_urls = _fetch_sitemap()
        candidates = _filter_candidate_urls(all_urls)

        if len(candidates) < TARGET_COUNT:
            raise RuntimeError(
                f"Not enough candidate URLs found ({len(candidates)} < {TARGET_COUNT}). "
                "The sitemap source may have changed."
            )

        selected_urls = candidates[:TARGET_COUNT]
        log.info(f"Selected {len(selected_urls)} URLs for the corpus")

        # 2. Prepare output paths
        urls_csv_path = paths.data("input", "urls.csv")
        raw_dir = paths.data("raw")
        raw_dir.mkdir(parents=True, exist_ok=True)

        # 3. Write URLs CSV (overwrite if exists)
        with urls_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["url"])
            writer.writeheader()
            for u in selected_urls:
                writer.writerow({"url": u})
        log.info(f"Wrote URL list to {urls_csv_path}")

        # 4. Download HTML snapshots in parallel
        download_futures = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for url in selected_urls:
                filename = _sanitize_filename(url)
                dest_file = raw_dir / filename
                future = executor.submit(_download_html, url, dest_file)
                download_futures[future] = dest_file

            for future in as_completed(download_futures):
                dest = download_futures[future]
                try:
                    future.result()
                except Exception as exc:
                    log.error(
                        f"Failed to download {dest.name}: {exc}",
                        error_code="ERR-010"
                    )
                    raise

        # 5. Compute checksums
        checksums_path = paths.data("checksums.txt")
        with checksums_path.open("w", encoding="utf-8") as chk_file:
            for html_file in sorted(raw_dir.iterdir()):
                if html_file.is_file():
                    h = _compute_sha256(html_file)
                    # Store path relative to the project root
                    rel_path = html_file.relative_to(paths.root)
                    chk_file.write(f"{h}  {rel_path}\\n")
        log.info(f"Wrote checksums to {checksums_path}")

        log.info("Corpus curation completed successfully")
        return 0

    except Exception as e:
        log.error(f"Corpus curation failed: {e}", error_code="ERR-100")
        raise

if __name__ == "__main__":
    sys.exit(main())
