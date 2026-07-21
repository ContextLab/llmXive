import os
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from config import ensure_directories

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0/"
OUTPUT_JSON = Path("data/raw/nvd_cve_merged.json.gz")
OUTPUT_SHA = Path("data/raw/nvd_cve_merged.json.gz.sha256")

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_nvd_feed(start_date: str, end_date: str) -> list:
    """Fetch CVE data from NVD API for a date range."""
    cves = []
    headers = {"User-Agent": "llmXive-Pipeline"}
    token = os.getenv("NVD_API_KEY")
    if token:
        headers["apiKey"] = token

    # NVD API pagination
    results_per_page = 2000
    start_index = 0
    
    print(f"Fetching NVD data from {start_date} to {end_date}...")

    while True:
        try:
            params = {
                "startIndex": start_index,
                "resultsPerPage": results_per_page,
                "pubStart": start_date,
                "pubEnd": end_date
            }
            response = requests.get(NVD_API_URL, headers=headers, params=params, timeout=120)
            
            if response.status_code == 403:
                # Rate limited, wait and retry
                print("Rate limited (403). Waiting 60 seconds before retry...")
                time.sleep(60)
                continue
            response.raise_for_status()
            
            data = response.json()
            vulns = data.get("vulnerabilities", [])
            
            if not vulns:
                break
            
            for v in vulns:
                cves.append(v)
            
            total_results = data.get("totalResults", 0)
            start_index += results_per_page
            
            if start_index >= total_results:
                break
            
            # NVD rate limit: 5 requests per 30 seconds
            # We wait 7 seconds to be safe
            time.sleep(7) 
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NVD data: {e}")
            # On network error, we fail loudly rather than returning partial data
            raise RuntimeError(f"Failed to fetch NVD data: {e}")
    
    return cves

def download_all_nvd_feeds():
    """Download CVE data for the last 5 years."""
    ensure_directories()
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5*365)
    
    start_str = start_date.strftime("%Y-%m-%dT00:00:00.000")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59.999")
    
    cves = fetch_nvd_feed(start_str, end_str)
    return cves

def deduplicate_cves(cves: list) -> list:
    """Deduplicate CVEs based on CVE ID."""
    seen_ids = set()
    unique_cves = []
    for cve in cves:
        cve_id = cve.get("cve", {}).get("id")
        if cve_id and cve_id not in seen_ids:
            seen_ids.add(cve_id)
            unique_cves.append(cve)
    return unique_cves

def save_and_compress(data: list, output_path: Path):
    """Save data as gzipped JSON."""
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        json.dump(data, f)

def generate_checksum(filepath: Path, checksum_path: Path):
    """Generate and save SHA256 checksum."""
    checksum = calculate_sha256(filepath)
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    print(f"Checksum generated: {checksum}")

def main():
    """Main entry point."""
    print("Starting NVD download process...")
    
    # Download
    cves = download_all_nvd_feeds()
    if not cves:
        raise RuntimeError("No CVE data downloaded.")
    
    # Deduplicate
    unique_cves = deduplicate_cves(cves)
    print(f"Downloaded {len(cves)} entries, {len(unique_cves)} unique.")
    
    # Save
    save_and_compress(unique_cves, OUTPUT_JSON)
    
    # Checksum
    generate_checksum(OUTPUT_JSON, OUTPUT_SHA)
    
    print(f"Successfully saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
