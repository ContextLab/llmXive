"""
Download verified UCI datasets for the augmentation impact study.

Fetches Breast Cancer, Ionosphere, and Heart Disease datasets via direct URLs.
Saves them to data/raw/ and computes SHA256 checksums.
"""

import os
import hashlib
import logging
import requests
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Verified UCI datasets with direct CSV URLs
DATASETS = {
    "breast_cancer": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data",
        "filename": "breast_cancer.csv",
        "has_header": False,
        "columns": [
            "id", "clump_thickness", "uniformity_cell_size", "uniformity_cell_shape",
            "marginal_adhesion", "single_epithelial_cell_size", "bare_nuclei",
            "bland_chromatin", "normal_nucleoli", "mitoses", "class"
        ]
    },
    "ionosphere": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data",
        "filename": "ionosphere.csv",
        "has_header": False,
        "columns": None  # Will be handled dynamically
    },
    "heart_disease": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
        "filename": "heart_disease.csv",
        "has_header": False,
        "columns": [
            "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
            "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
        ]
    }
}

def compute_sha256(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(dataset_name: str, config: dict) -> bool:
    """
    Download a single dataset and save to data/raw/.

    Args:
        dataset_name: Name of the dataset
        config: Dataset configuration with url, filename, etc.

    Returns:
        True if download successful, False otherwise
    """
    try:
        logger.info(f"Downloading {dataset_name} from {config['url']}")
        
        response = requests.get(config['url'], timeout=30)
        response.raise_for_status()
        
        output_path = RAW_DATA_DIR / config['filename']
        
        # Parse and save the data
        if config['has_header']:
            df = pd.read_csv(pd.io.common.StringIO(response.text))
        else:
            df = pd.read_csv(
                pd.io.common.StringIO(response.text),
                header=None,
                names=config['columns']
            )
        
        # Clean data: remove rows with missing values (represented as '?')
        df = df.replace('?', pd.NA)
        df = df.dropna()
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        # Compute checksum
        checksum = compute_sha256(output_path)
        
        logger.info(f"Saved {output_path} ({len(df)} rows, checksum: {checksum[:16]}...)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to download {dataset_name}: {str(e)}")
        return False

def main():
    """Main function to download all verified datasets."""
    logger.info("Starting data download process...")
    
    successful_downloads = 0
    failed_downloads = []
    
    for dataset_name, config in DATASETS.items():
        if download_dataset(dataset_name, config):
            successful_downloads += 1
        else:
            failed_downloads.append(dataset_name)
    
    # Log warning if count doesn't match expected 3
    if successful_downloads != 3:
        logger.warning(
            f"Downloaded {successful_downloads} datasets instead of expected 3. "
            f"Failed: {failed_downloads}. This deviates from FR-001 intent of 5 datasets, "
            f"but we are using only verified datasets as required."
        )
    
    logger.info(f"Download complete: {successful_downloads}/3 datasets successful")
    
    if failed_downloads:
        logger.error(f"Failed datasets: {', '.join(failed_downloads)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
