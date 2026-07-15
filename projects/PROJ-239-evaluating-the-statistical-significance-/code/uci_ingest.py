"""
UCI Online Retail Data Ingestion Script.

This script downloads the UCI Online Retail dataset from the canonical source,
saves it to the project's raw data directory, computes a SHA-256 checksum,
and performs a basic PII scan for email patterns.

Dependencies:
    - pandas
    - hashlib
    - re
    - os
    - sys
"""
import os
import sys
import re
import hashlib
import warnings
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install via 'pip install pandas'.")
    sys.exit(1)

# Constants
# Using the direct CSV mirror which is widely used for this dataset to avoid
# engine dependencies (openpyxl/xlrd) required for the XLSX version.
# If this URL fails, the script will attempt the canonical XLSX source as a fallback.
CSV_URL = "https://raw.githubusercontent.com/eamonn/UCI-Online-Retail/master/Online%20Retail.csv"
CANONICAL_XLSX_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"

OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "uci_online_retail.csv"
CHECKSUM_FILE = Path("data/checksums.txt")

# PII Regex for email
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

def ensure_dirs():
    """Create output directories if they do not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure data directory exists for checksum file
    Path("data").mkdir(parents=True, exist_ok=True)

def download_data(url: str, output_path: Path) -> None:
    """Download the dataset from the given URL using urllib."""
    print(f"Downloading data from {url}...")
    try:
        import urllib.request
        urllib.request.urlretrieve(url, str(output_path))
        print(f"Data downloaded successfully to {output_path}")
    except Exception as e:
        print(f"Error downloading data: {e}")
        raise

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(file_path: Path, checksum: str) -> None:
    """Save the checksum to a text file."""
    with open(CHECKSUM_FILE, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    print(f"Checksum saved to {CHECKSUM_FILE}")

def scan_pii(file_path: Path) -> int:
    """
    Scan the file for potential PII (email addresses).
    Returns the count of matches found.
    """
    print(f"Scanning {file_path} for PII (email patterns)...")
    count = 0
    try:
        # Read as text. The dataset might be large, so we read line by line.
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                matches = EMAIL_PATTERN.findall(line)
                count += len(matches)
    except Exception as e:
        print(f"Error scanning file: {e}")
        return -1

    if count > 0:
        print(f"Warning: Found {count} potential email addresses in the dataset.")
        print("This dataset may contain PII. Ensure compliance with data privacy regulations.")
    else:
        print("No email patterns found.")

    return count

def main():
    """Main execution function."""
    print("--- UCI Online Retail Data Ingestion ---")

    # 1. Ensure directories
    ensure_dirs()

    # 2. Download data
    # We attempt the CSV first to minimize dependencies.
    data_downloaded = False
    if not OUTPUT_FILE.exists():
        try:
            download_data(CSV_URL, OUTPUT_FILE)
            data_downloaded = True
        except Exception as e:
            print(f"CSV download failed ({e}). Attempting XLSX fallback...")
            xlsx_path = OUTPUT_FILE.with_suffix('.xlsx')
            try:
                download_data(CANONICAL_URL, xlsx_path)
                print("Converting XLSX to CSV...")
                # Check for openpyxl
                try:
                    df = pd.read_excel(xlsx_path)
                    df.to_csv(OUTPUT_FILE, index=False)
                    xlsx_path.unlink()
                    print("Conversion complete.")
                    data_downloaded = True
                except ImportError:
                    print("Error: openpyxl is required to read XLSX files. Install via 'pip install openpyxl'.")
                    sys.exit(1)
            except Exception as e2:
                print(f"Both download attempts failed: {e2}")
                sys.exit(1)
    else:
        print(f"Data file {OUTPUT_FILE} already exists. Skipping download.")

    if not data_downloaded and not OUTPUT_FILE.exists():
        print("Error: Data file could not be retrieved.")
        sys.exit(1)

    # 3. Compute Checksum
    checksum = compute_sha256(OUTPUT_FILE)
    save_checksum(OUTPUT_FILE, checksum)

    # 4. PII Scan
    pii_count = scan_pii(OUTPUT_FILE)

    print("--- Ingestion Complete ---")
    return 0

if __name__ == "__main__":
    sys.exit(main())