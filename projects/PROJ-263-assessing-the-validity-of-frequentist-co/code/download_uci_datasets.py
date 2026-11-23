import os
import sys
import csv
import logging
import urllib.request
import ssl
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dataset definitions mapping names to UCI URLs and expected file paths
DATASETS = {
    "wine": {
        "url": "https://archive.ics.uci.edu/static/public/105/wine.csv",
        "file": "wine.csv",
        "description": "Wine dataset"
    },
    "wine_quality_red": {
        "url": "https://archive.ics.uci.edu/static/public/186/wine+quality+red.csv",
        "file": "wine_quality_red.csv",
        "description": "Wine Quality Red dataset"
    },
    "wine_quality_white": {
        "url": "https://archive.ics.uci.edu/static/public/186/wine+quality+white.csv",
        "file": "wine_quality_white.csv",
        "description": "Wine Quality White dataset"
    },
    "ionosphere": {
        "url": "https://archive.ics.uci.edu/static/public/47/ionosphere.csv",
        "file": "ionosphere.csv",
        "description": "Ionosphere dataset"
    },
    "heart_disease_cleveland": {
        "url": "https://archive.ics.uci.edu/static/public/45/heart+disease.csv",
        "file": "heart_disease_cleveland.csv",
        "description": "Heart Disease (Cleveland) dataset"
    }
}

def ensure_data_directory(raw_data_dir: Path) -> None:
    """Ensure the raw data directory exists."""
    if not raw_data_dir.exists():
        raw_data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created raw data directory: {raw_data_dir}")
    else:
        logger.info(f"Raw data directory already exists: {raw_data_dir}")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_dataset(url: str, file_path: Path, dataset_name: str) -> bool:
    """
    Fetch a dataset from UCI via HTTP.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Fetching {dataset_name} from {url}")
    try:
        # Create an SSL context that does not verify certificates to handle
        # potential self-signed issues on some UCI mirrors, though standard
        # UCI URLs usually work with default.
        context = ssl.create_default_context()
        
        with urllib.request.urlopen(url, context=context, timeout=30) as response:
            with open(file_path, 'wb') as out_file:
                # Read in chunks to handle large files gracefully
                chunk_size = 1024 * 1024  # 1 MB
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
        
        checksum = compute_sha256(file_path)
        logger.info(f"Successfully downloaded {dataset_name} to {file_path} (SHA256: {checksum[:16]}...)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to fetch {dataset_name}: {e}")
        return False

def clean_missing_values(file_path: Path) -> None:
    """
    Remove rows with missing values (empty fields) from the CSV.
    Modifies the file in-place.
    """
    logger.info(f"Cleaning missing values from {file_path}")
    temp_path = file_path.with_suffix('.tmp')
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as infile, \
             open(temp_path, 'w', newline='', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            header = next(reader, None)
            if header:
                writer.writerow(header)
            
            row_count = 0
            cleaned_count = 0
            for row in reader:
                row_count += 1
                # Check if any field is empty or just whitespace
                if any(field.strip() == '' for field in row):
                    continue
                writer.writerow(row)
                cleaned_count += 1
                
        # Replace original with cleaned
        temp_path.replace(file_path)
        logger.info(f"Cleaned {file_path}: {row_count} rows processed, {cleaned_count} rows kept")
        
    except Exception as e:
        logger.error(f"Error cleaning missing values in {file_path}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise

def main():
    """Main entry point for downloading UCI datasets."""
    # Determine project root (assuming this script is in code/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    raw_data_dir = project_root / "data" / "raw"
    
    ensure_data_directory(raw_data_dir)
    
    success_count = 0
    total_count = len(DATASETS)
    
    for name, config in DATASETS.items():
        file_path = raw_data_dir / config["file"]
        
        # Skip if already exists (optional: add force flag if needed)
        if file_path.exists():
            logger.info(f"Skipping {name}: {file_path} already exists")
            success_count += 1
            continue
        
        if fetch_dataset(config["url"], file_path, config["description"]):
            try:
                clean_missing_values(file_path)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to clean {name}: {e}")
                # Optionally remove the corrupted file
                file_path.unlink()
        else:
            logger.warning(f"Skipping cleaning for {name} due to download failure")
    
    logger.info(f"Download complete: {success_count}/{total_count} datasets processed successfully")
    
    if success_count < total_count:
        sys.exit(1)

if __name__ == "__main__":
    main()
