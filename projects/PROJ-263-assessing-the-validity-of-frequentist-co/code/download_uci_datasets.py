"""
UCI Dataset Downloader Module.

Fetches real numeric datasets from the UCI Machine Learning Repository via HTTP
and saves them to data/raw/.

Specific datasets fetched:
- Wine
- Wine Quality Red
- Wine Quality White
- Ionosphere
- Heart Disease (Cleveland)
"""

import os
import sys
import csv
import logging
import urllib.request
import ssl
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a custom SSL context that verifies certificates
# but allows older TLS versions if necessary for some UCI endpoints
try:
    ssl_context = ssl.create_default_context()
except Exception:
    ssl_context = None

# Define the datasets to fetch with their UCI URLs
# These are direct links to the data files or repository pages
DATASETS = {
    "wine": {
        "name": "Wine",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "description": "Chemical analysis of wines grown in the same region in Italy but derived from three different cultivars.",
        "has_header": False,
        "class_col": 0,
        "output_name": "wine.csv"
    },
    "wine_quality_red": {
        "name": "Wine Quality Red",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
        "description": "Quality of red Portuguese 'Vinho Verde' wine.",
        "has_header": True,
        "class_col": -1,
        "output_name": "wine_quality_red.csv",
        "delimiter": ";"
    },
    "wine_quality_white": {
        "name": "Wine Quality White",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
        "description": "Quality of white Portuguese 'Vinho Verde' wine.",
        "has_header": True,
        "class_col": -1,
        "output_name": "wine_quality_white.csv",
        "delimiter": ";"
    },
    "ionosphere": {
        "name": "Ionosphere",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data",
        "description": "Radar data collected by a system in Goose Bay, Labrador.",
        "has_header": False,
        "class_col": -1,
        "output_name": "ionosphere.csv"
    },
    "heart_cleveland": {
        "name": "Heart Disease (Cleveland)",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
        "description": "Heart disease data from the Cleveland Clinic Foundation.",
        "has_header": False,
        "class_col": 13,  # The 'num' column (diagnosis) is at index 13
        "output_name": "heart_cleveland.csv"
    }
}

def ensure_data_directory(base_dir: str = "data/raw") -> Path:
    """Ensure the raw data directory exists."""
    raw_dir = Path(base_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directory exists: {raw_dir}")
    return raw_dir

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(dataset_key: str, raw_dir: Path) -> Tuple[bool, str]:
    """
    Fetch a single dataset from UCI and save it to raw_dir.

    Args:
        dataset_key: Key from DATASETS dict
        raw_dir: Directory to save the file

    Returns:
        Tuple of (success: bool, message: str)
    """
    dataset_info = DATASETS[dataset_key]
    url = dataset_info["url"]
    output_name = dataset_info["output_name"]
    output_path = raw_dir / output_name

    # Skip if file already exists
    if output_path.exists():
        logger.info(f"File {output_path} already exists. Skipping download.")
        checksum = compute_sha256(output_path)
        return True, f"Already exists (checksum: {checksum[:16]}...)"

    logger.info(f"Fetching {dataset_info['name']} from {url}...")

    try:
        # Create a request with headers to mimic a browser
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

        # Handle SSL context if available
        if ssl_context:
            response = urllib.request.urlopen(req, context=ssl_context, timeout=30)
        else:
            response = urllib.request.urlopen(req, timeout=30)

        # Read the content
        content = response.read()

        # Decode if necessary (UCI usually returns ASCII/UTF-8)
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            text_content = content.decode('latin-1')

        # Write to file
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write(text_content)

        # Compute checksum
        checksum = compute_sha256(output_path)

        logger.info(f"Successfully downloaded {dataset_info['name']}. "
                    f"Saved to {output_path} (checksum: {checksum[:16]}...)")

        return True, f"Downloaded successfully (checksum: {checksum[:16]}...)"

    except urllib.error.URLError as e:
        error_msg = f"Failed to fetch {dataset_info['name']}: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error fetching {dataset_info['name']}: {e}"
        logger.error(error_msg)
        return False, error_msg

def clean_missing_values(input_path: Path, output_path: Path, delimiter: str = ",") -> bool:
    """
    Remove rows with missing values (represented as '?', '', or NaN).
    This is a simple pass to ensure data cleanliness.

    Args:
        input_path: Path to the raw downloaded file
        output_path: Path to save the cleaned file
        delimiter: CSV delimiter

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(input_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile, delimiter=delimiter)
            rows = list(reader)

        if not rows:
            logger.warning(f"File {input_path} is empty.")
            return False

        # Identify header if present (simple heuristic: first row has non-numeric in class col if needed)
        # For now, we just filter out rows with '?' or empty strings in numeric columns
        cleaned_rows = []
        missing_count = 0

        for i, row in enumerate(rows):
            # Skip rows that are entirely empty or contain '?'
            if all(cell.strip() == '' or cell.strip() == '?' for cell in row):
                missing_count += 1
                continue

            # Check for missing values in numeric columns
            has_missing = False
            for cell in row:
                cell_clean = cell.strip()
                if cell_clean == '' or cell_clean == '?':
                    has_missing = True
                    break

            if not has_missing:
                cleaned_rows.append(row)
            else:
                missing_count += 1

        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            writer.writerows(cleaned_rows)

        if missing_count > 0:
            logger.info(f"Removed {missing_count} rows with missing values from {input_path.name}")
        else:
            logger.info(f"No missing values found in {input_path.name}")

        return True

    except Exception as e:
        logger.error(f"Error cleaning missing values in {input_path}: {e}")
        return False

def main():
    """Main entry point to download all specified UCI datasets."""
    logger.info("Starting UCI Dataset Downloader...")

    raw_dir = ensure_data_directory()
    results = {}

    for key, info in DATASETS.items():
        success, message = fetch_dataset(key, raw_dir)
        results[key] = {
            "success": success,
            "message": message,
            "path": str(raw_dir / info["output_name"])
        }

        if not success:
            logger.error(f"Failed to process {key}: {message}")

    # Log summary
    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)
    logger.info(f"Download complete: {success_count}/{total_count} datasets fetched successfully.")

    # Return exit code based on success
    if success_count == total_count:
        logger.info("All datasets downloaded successfully.")
        return 0
    else:
        logger.error("Some datasets failed to download.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
