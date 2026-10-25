"""
curate_corpus.py

Script to create a deterministic corpus of ≥ 300 reachable URLs that
point to public A/B test summaries. The script performs the following
steps:

1. Retrieves one or more sitemaps that list many case‑study or blog‑post
   pages from a set of known A/B‑testing platforms (Optimizely,
   ConversionXL, VWO, Unbounce). The list of sitemap URLs is defined in
   ``SITEMAP_SOURCES``.
2. Filters the URLs to keep only those that appear to be case‑study,
   blog, or experiment pages (heuristic based on a set of keywords).
3. Takes the first ``TARGET_COUNT`` URLs, downloads each page, and writes
   the raw HTML to ``data/raw/<sanitized_name>.html``.
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
# List of publicly available sitemaps that contain many A/B‑test related pages.
SITEMAP_SOURCES = [
    "https://www.optimizely.com/sitemap.xml",
    "https://www.conversionxl.com/sitemap.xml",
    "https://vwo.com/sitemap.xml",
    "https://unbounce.com/sitemap.xml",
]

# The number of URLs we need in the final corpus.
TARGET_COUNT = 300

# Concurrency settings for downloading HTML pages.
MAX_WORKERS = 10
TIMEOUT = 20  # seconds per HTTP request

# Keywords used to identify candidate A/B‑test summary pages.
CANDIDATE_KEYWORDS = [
    "case-study",
    "case-studies",
    "blog",
    "ab-test",
    "abtest",
    "experiment",
    "a-b-test",
]

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

def _fetch_sitemap(sitemap_url: str) -> List[str]:
    """
    Download a sitemap XML and return a list of URLs contained within.
    This implementation is robust to the presence or absence of XML
    namespaces.
    """
    log.info(f"Fetching sitemap from {sitemap_url}")
    resp = requests.get(sitemap_url, timeout=TIMEOUT)
    resp.raise_for_status()
    # Parse XML; use ``.//{*}url`` to match any namespace
    root = ET.fromstring(resp.content)

    urls: List[str] = []
    for url_elem in root.findall(".//{*}url"):
        loc = url_elem.find("{*}loc")
        if loc is not None and loc.text:
            urls.append(loc.text.strip())
    log.info(f"Found {len(urls)} URLs in sitemap {sitemap_url}")
    return urls

def _gather_all_urls() -> List[str]:
    """
    Iterate over all sitemap sources, collect URLs, and return the
    combined list.
    """
    all_urls: List[str] = []
    for src in SITEMAP_SOURCES:
        try:
            urls = _fetch_sitemap(src)
            all_urls.extend(urls)
        except Exception as e:
            log.warning(f"Failed to fetch sitemap {src}: {e}")
    return all_urls

def _filter_candidate_urls(urls: List[str]) -> List[str]:
    """
    Keep URLs that plausibly point to A/B‑test case studies, blogs,
    or experiment write‑ups.
    """
    lowered = [u.lower() for u in urls]
    candidates = [
        u for u in lowered
        if any(kw in u for kw in CANDIDATE_KEYWORDS)
    ]
    log.info(f"Filtered down to {len(candidates)} candidate URLs after keyword scan")
    # Preserve original case‑sensitive URLs while deduplicating
    seen = set()
    ordered: List[str] = []
    for orig, low in zip(urls, lowered):
        if low in candidates and low not in seen:
            seen.add(low)
            ordered.append(orig)
    return sorted(set(ordered))

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
        # 1. Load sitemaps and collect candidate URLs
        all_urls = _gather_all_urls()
        candidates = _filter_candidate_urls(all_urls)

        if len(candidates) < TARGET_COUNT:
            raise RuntimeError(
                f"Not enough candidate URLs found ({len(candidates)} < {TARGET_COUNT}). "
                "Consider adding more sitemap sources."
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
                    log.error(f"Failed to download {dest.name}: {exc}")
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
        log.error(f"Corpus curation failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
