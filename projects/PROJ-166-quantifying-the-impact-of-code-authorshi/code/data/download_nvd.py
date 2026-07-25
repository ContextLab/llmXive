import os
import gzip
import hashlib
import json
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path for imports
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0/"
OUTPUT_JSON = Path("data/raw/nvd_cve_merged.json.gz")
OUTPUT_SHA = Path("data/raw/nvd_cve_merged.json.gz.sha256")

# NVD API constraints
RESULTS_PER_PAGE = 2000
RATE_LIMIT_DELAY = 7.0  # seconds between requests to stay under 5 req/30s
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 60  # seconds

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_nvd_feed(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Fetch CVE data from NVD API for a date range with pagination and rate limiting."""
    cves = []
    headers = {"User-Agent": "llmXive-Pipeline"}
    token = os.getenv("NVD_API_KEY")
    if token:
        headers["apiKey"] = token

    start_index = 0
    logger.info(f"Fetching NVD data from {start_date} to {end_date}...")

    while True:
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                params = {
                    "startIndex": start_index,
                    "resultsPerPage": RESULTS_PER_PAGE,
                    "pubStart": start_date,
                    "pubEnd": end_date
                }
                response = requests.get(
                    NVD_API_URL, 
                    headers=headers, 
                    params=params, 
                    timeout=120
                )
                
                if response.status_code == 403:
                    # Rate limited, wait with exponential backoff
                    wait_time = RETRY_BACKOFF_BASE * (2 ** retry_count)
                    logger.warning(f"Rate limited (403). Waiting {wait_time}s before retry ({retry_count+1}/{MAX_RETRIES})...")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue
                
                if response.status_code == 429:
                    # Too many requests, wait
                    wait_time = RETRY_BACKOFF_BASE * (2 ** retry_count)
                    logger.warning(f"Too many requests (429). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    retry_count += 1
                    continue

                response.raise_for_status()
                
                data = response.json()
                vulns = data.get("vulnerabilities", [])
                
                if not vulns:
                    # No more data
                    logger.info("No more vulnerabilities found in this range.")
                    break
                
                for v in vulns:
                    cves.append(v)
                
                total_results = data.get("totalResults", 0)
                start_index += RESULTS_PER_PAGE
                
                logger.info(f"Processed {start_index}/{total_results} results...")
                
                if start_index >= total_results:
                    break
                
                # NVD rate limit: 5 requests per 30 seconds
                # We wait 7 seconds to be safe
                time.sleep(RATE_LIMIT_DELAY) 
                
                break  # Success, exit retry loop

            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < MAX_RETRIES:
                    wait_time = RETRY_BACKOFF_BASE * (2 ** (retry_count - 1))
                    logger.warning(f"Network error: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Fail loudly after max retries
                    logger.error(f"Failed to fetch NVD data after {MAX_RETRIES} retries: {e}")
                    raise RuntimeError(f"Failed to fetch NVD data: {e}")
        
        if start_index >= total_results or not vulns:
            break

    return cves

def download_all_nvd_feeds() -> List[Dict[str, Any]]:
    """Download CVE data for the last 5 years (historical range)."""
    ensure_directories()
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5 * 365)
    
    start_str = start_date.strftime("%Y-%m-%dT00:00:00.000")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59.999")
    
    cves = fetch_nvd_feed(start_str, end_str)
    return cves

def deduplicate_cves(cves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate CVEs based on CVE ID."""
    seen_ids = set()
    unique_cves = []
    for cve in cves:
        cve_id = cve.get("cve", {}).get("id")
        if cve_id and cve_id not in seen_ids:
            seen_ids.add(cve_id)
            unique_cves.append(cve)
        elif cve_id and cve_id in seen_ids:
            logger.debug(f"Skipping duplicate CVE: {cve_id}")
    return unique_cves

def save_and_compress(data: List[Dict[str, Any]], output_path: Path):
    """Save data as gzipped JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} entries to {output_path}")

def generate_checksum(filepath: Path, checksum_path: Path):
    """Generate and save SHA256 checksum."""
    checksum = calculate_sha256(filepath)
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    logger.info(f"Checksum generated: {checksum} -> {checksum_path}")

def main():
    """Main entry point."""
    logger.info("Starting NVD download process...")
    
    # Download
    cves = download_all_nvd_feeds()
    if not cves:
        raise RuntimeError("No CVE data downloaded.")
    
    # Deduplicate
    unique_cves = deduplicate_cves(cves)
    logger.info(f"Downloaded {len(cves)} entries, {len(unique_cves)} unique.")
    
    if len(unique_cves) == 0:
        raise RuntimeError("No unique CVE data found after deduplication.")
    
    # Save
    save_and_compress(unique_cves, OUTPUT_JSON)
    
    # Checksum
    generate_checksum(OUTPUT_JSON, OUTPUT_SHA)
    
    logger.info(f"Successfully saved to {OUTPUT_JSON}")
    logger.info(f"Checksum saved to {OUTPUT_SHA}")

if __name__ == "__main__":
    main()
