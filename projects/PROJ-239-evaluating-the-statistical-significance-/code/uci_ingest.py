"""
UCI Online Retail Data Ingestion Script.

This script downloads the UCI Online Retail dataset from the canonical source,
saves it to the project's raw data directory, computes a SHA-256 checksum,
and performs a basic PII scan for email patterns.

Dependencies:
    requests (for downloading)
    pandas (for CSV handling)
    hashlib (for checksum)
    re (for PII scanning)
"""
import os
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd
import requests

# Canonical URL for UCI Online Retail dataset (Excel file)
# Note: UCI often hosts as .xlsx. We will download and convert to CSV.
# If the direct link changes, this URL should be updated.
# Using the raw data link from the UCI repository or a reliable mirror.
# The dataset is "Online Retail II" (two sheets), but we will fetch the main one.
# Official URL: https://archive.ics.uci.edu/ml/machine-learning-databases/005022/Online%20Retail.xlsx
# However, to ensure stability, we use the raw GitHub mirror if available or the direct UCI link.
# Let's use the direct UCI archive link.
DATA_URL = "https://archive.ics.uci.edu/static/public/5022/online+retail+ii.zip"

# Fallback or alternative: The dataset is often available as a zip containing the Excel file.
# We will download the zip, extract the Excel, and save as CSV.

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_FILE = PROJECT_ROOT / "data" / "checksums.txt"

# Output file names
OUTPUT_CSV = DATA_RAW_DIR / "uci_online_retail.csv"
ZIP_FILE = DATA_RAW_DIR / "uci_online_retail_raw.zip"
EXCEL_FILE = DATA_RAW_DIR / "Online Retail II.xlsx"

PII_REGEX_EMAIL = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

def download_file(url, dest_path):
    """Downloads a file from the given URL to the destination path."""
    print(f"Downloading data from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {dest_path}")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        raise

def extract_zip(zip_path, extract_to):
    """Extracts a zip file to the specified directory."""
    import zipfile
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted to {extract_to}")

def compute_sha256(file_path):
    """Computes the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_pii(file_path):
    """Scans a CSV file for potential PII (emails) and returns counts."""
    print(f"Scanning {file_path} for PII (email patterns)...")
    found_emails = []
    try:
        # Read in chunks to handle large files if necessary
        for chunk in pd.read_csv(file_path, chunksize=10000):
            # Convert all columns to string and search
            chunk_str = chunk.astype(str)
            for col in chunk_str.columns:
                matches = chunk_str[col].str.contains(PII_REGEX_EMAIL, regex=True, na=False)
                if matches.any():
                    # Extract actual matches for logging (limit to first 5)
                    sample_matches = chunk_str[col][matches].unique()[:5]
                    found_emails.extend([f"{col}: {m}" for m in sample_matches])
    except Exception as e:
        print(f"Error during PII scan: {e}")
        return []
    
    # Deduplicate and limit output
    unique_emails = list(set(found_emails))
    return unique_emails

def main():
    """Main execution flow."""
    # Ensure directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Download
    try:
        download_file(DATA_URL, ZIP_FILE)
    except Exception as e:
        print(f"Failed to download data. Aborting.")
        sys.exit(1)

    # 2. Extract
    try:
        extract_zip(ZIP_FILE, DATA_RAW_DIR)
    except Exception as e:
        print(f"Failed to extract zip. Aborting.")
        sys.exit(1)

    # Locate the Excel file (it might be named slightly differently)
    excel_files = list(DATA_RAW_DIR.glob("*.xlsx"))
    if not excel_files:
        print("No Excel file found after extraction.")
        sys.exit(1)
    
    source_excel = excel_files[0]
    print(f"Found Excel file: {source_excel.name}")

    # 3. Convert to CSV
    try:
        # The UCI dataset has multiple sheets. We'll read the first one or 'Online Retail II'
        # If the sheet name is unknown, we try the first sheet.
        df = pd.read_excel(source_excel, sheet_name=0) 
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"Saved CSV to {OUTPUT_CSV}")
    except Exception as e:
        print(f"Failed to convert to CSV: {e}")
        sys.exit(1)

    # 4. Compute Checksum
    checksum = compute_sha256(OUTPUT_CSV)
    print(f"SHA-256 Checksum: {checksum}")

    # Save checksum
    with open(CHECKSUMS_FILE, 'a') as f:
        f.write(f"{OUTPUT_CSV.name}:{checksum}\n")
    print(f"Checksum saved to {CHECKSUMS_FILE}")

    # 5. PII Scan
    pii_results = scan_pii(OUTPUT_CSV)
    if pii_results:
        print(f"WARNING: Potential PII (emails) detected. Samples found:")
        for item in pii_results:
            print(f"  - {item}")
    else:
        print("No email patterns detected in the dataset.")

    # Cleanup intermediate files (optional but good practice)
    # os.remove(ZIP_FILE)
    # os.remove(source_excel)
    # print("Cleaned up intermediate files.")

    print("Ingestion complete.")

if __name__ == "__main__":
    main()
