"""
curate_corpus.py

Script to create a deterministic corpus of >= 300 reachable URLs that
point to public A/B test summaries. 

The script:
1. Recursively parses sitemaps from known A/B testing platforms to find URLs.
2. Filters URLs based on keywords identifying case studies or experiments.
3. Downloads pages until the TARGET_COUNT of successful HTML snapshots is reached.
4. Writes the final list of successful URLs to data/input/urls.csv.
5. Stores raw HTML snapshots under data/raw/.
6. Generates data/checksums.txt with SHA-256 hashes of all snapshots.

The script is idempotent: it checks for existing files before downloading.
"""
import csv
import hashlib
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Set

import requests
import xml.etree.ElementTree as ET

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
SITEMAP_SOURCES = [
    "https://www.optimizely.com/sitemap.xml",
    "https://vwo.com/sitemap.xml",
    "https://www.conversionxl.com/sitemap.xml",
    "https://unbounce.com/sitemap.xml",
]

TARGET_COUNT = 300
MAX_WORKERS = 10
TIMEOUT = 20

CANDIDATE_KEYWORDS = [
    "case-study",
    "case-studies",
    "blog",
    "ab-test",
    "abtest",
    "experiment",
    "a-b-test",
    "optimization-result",
    "conversion-rate",
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sanitize_filename(url: str) -> str:
    path = re.sub(r"^https?://", "", url)
    path = re.sub(r"[^A-Za-z0-9]+", "_", path)
    return path[:200] + ".html"

def _fetch_sitemap_recursive(sitemap_url: str, visited: Set[str]) -> List[str]:
    """
    Recursively fetch sitemaps and extract all <loc> URLs.
    """
    if sitemap_url in visited:
        return []
    visited.add(sitemap_url)

    urls: List[str] = []
    try:
        log.info(f"Fetching sitemap: {sitemap_url}")
        resp = requests.get(sitemap_url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        # Find all loc tags regardless of namespace
        for loc_elem in root.findall(".//{*}loc"):
            if loc_elem.text:
                loc_text = loc_elem.text.strip()
                if loc_text.endswith(".xml"):
                    # Recurse into child sitemaps
                    urls.extend(_fetch_sitemap_recursive(loc_text, visited))
                else:
                    urls.append(loc_text)
    except Exception as e:
        log.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
    
    return urls

def _gather_all_candidates() -> List[str]:
    all_urls: List[str] = []
    visited: Set[str] = set()
    for src in SITEMAP_SOURCES:
        all_urls.extend(_fetch_sitemap_recursive(src, visited))
    
    # Deduplicate and filter
    seen = set()
    candidates: List[str] = []
    for u in all_urls:
        low = u.lower()
        if low not in seen and any(kw in low for kw in CANDIDATE_KEYWORDS):
            seen.add(low)
            candidates.append(u)
    
    log.info(f"Gathered {len(candidates)} total candidate URLs")
    return sorted(candidates)

def _download_html(url: str, dest_path: Path) -> bool:
    """
    Download a single URL. Return True if successful, False otherwise.
    """
    if dest_path.exists():
        return True

    try:
        resp = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        if "text/html" not in resp.headers.get("Content-Type", "").lower():
            return False
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(resp.content)
        return True
    except Exception as e:
        log.debug(f"Failed to download {url}: {e}")
        return False

def _compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> int:
    try:
        # 1. Gather candidates
        candidates = _gather_all_candidates()
        if not candidates:
            raise RuntimeError("No candidate URLs found from sitemaps.")

        # 2. Download until TARGET_COUNT is reached
        raw_dir = paths.data("raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        successful_urls: List[str] = []
        
        # Process in batches to avoid overloading but keep speed
        batch_size = 100
        for i in range(0, len(candidates), batch_size):
            if len(successful_urls) >= TARGET_COUNT:
                break
                
            batch = candidates[i : i + batch_size]
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                future_to_url = {
                    executor.submit(_download_html, url, raw_dir / _sanitize_filename(url)): url 
                    for url in batch
                }
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    if future.result():
                        successful_urls.append(url)
                    if len(successful_urls) >= TARGET_COUNT:
                        # We can't easily stop the executor, but we can stop adding to our list
                        pass

        # Trim to exact target
        final_urls = successful_urls[:TARGET_COUNT]
        if len(final_urls) < TARGET_COUNT:
            raise RuntimeError(f"Could only download {len(final_urls)}/{TARGET_COUNT} reachable URLs.")

        # 3. Write URLs CSV
        urls_csv_path = paths.data("input", "urls.csv")
        urls_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with urls_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["url"])
            writer.writeheader()
            for u in final_urls:
                writer.writerow({"url": u})
        log.info(f"Wrote {len(final_urls)} URLs to {urls_csv_path}")

        # 4. Compute checksums for the final set
        checksums_path = paths.data("checksums.txt")
        with checksums_path.open("w", encoding="utf-8") as chk_file:
            # We only checksum the files corresponding to the final_urls
            for url in final_urls:
                filename = _sanitize_filename(url)
                html_file = raw_dir / filename
                if html_file.exists():
                    h = _compute_sha256(html_file)
                    rel_path = html_file.relative_to(paths.root)
                    chk_file.write(f"{h}  {rel_path}\n")
        
        log.info(f"Wrote checksums to {checksums_path}")
        log.info("Corpus curation completed successfully")
        return 0

    except Exception as e:
        log.error(f"Corpus curation failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())