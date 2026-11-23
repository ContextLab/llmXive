import os
import sys
import time
import socket
import urllib.request
import urllib.error
import logging

DATA_DIR = "data/raw"
OUTPUT_FILE = os.path.join(DATA_DIR, "zeta_zeros.csv")
VERIFIED_URLS = ["http://www.lmfdb.org/data/zeros/", "https://www.dtm.uci.edu/zeroes/"]

def verify_url_reachability(url):
    """Checks if a URL is reachable."""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return True
    except (urllib.error.URLError, socket.timeout):
        return False

def verify_sources():
    """Verifies the availability of zeta zero sources."""
    reachable_urls = [url for url in VERIFIED_URLS if verify_url_reachability(url)]
    if not reachable_urls:
        logging.error("No verified zeta zero sources are reachable. Halting.")
        sys.exit(1)  # Exit if no source is available
    return reachable_urls

def parse_zeta_zero_line(line):
    """Parses a line from the zeta zero data file."""
    try:
        real, imag = map(float, line.split())
        return real, imag
    except ValueError:
        logging.warning(f"Skipping malformed line: {line}")
        return None, None

def fetch_zeta_zeros(url):
    """Fetches zeta zeros from a given URL."""
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            zeros = []
            for line in data.splitlines():
                real, imag = parse_zeta_zero_line(line)
                if real is not None and imag is not None:
                    zeros.append((real, imag))
            return zeros
    except Exception as e:
        logging.error(f"Error fetching zeta zeros from {url}: {e}")
        return []

def ingest_zeros_sample():
    """Ingests zeta zeros from verified sources."""
    reachable_urls = verify_sources()
    all_zeros = []
    for url in reachable_urls:
        zeros = fetch_zeta_zeros(url)
        all_zeros.extend(zeros)

    with open(OUTPUT_FILE, 'w') as f:
        for real, imag in all_zeros:
            f.write(f"{real},{imag}\n")

    logging.info(f"Zeta zeros ingested and saved to {OUTPUT_FILE}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    ensure_directories(DATA_DIR)
    ingest_zeros_sample()

def ensure_directories(directory):
    """Ensures that the given directory exists."""
    os.makedirs(directory, exist_ok=True)
    

if __name__ == "__main__":
    main()