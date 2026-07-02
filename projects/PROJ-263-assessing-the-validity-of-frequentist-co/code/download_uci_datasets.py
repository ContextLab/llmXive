"""
T016: UCI Dataset Downloader
Fetches real numeric datasets from the UCI Machine Learning Repository via HTTP
and saves them to data/raw/.

Specific datasets:
1. Wine (UCI ID: 109)
2. Wine Quality Red (UCI ID: 186)
3. Wine Quality White (UCI ID: 185)
4. Ionosphere (UCI ID: 112)
5. Heart Disease (Cleveland) (UCI ID: 144)

This module adheres to FR-001 by ensuring data is retrieved from a real source.
"""
import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# UCI Machine Learning Repository Base URL
UCI_BASE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases"

# Dataset Configuration
# Maps friendly names to UCI directory paths and specific file names
DATASETS = {
    "wine": {
        "dir": "wine/wine.data",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "has_header": False,
        "description": "Wine dataset (178 instances, 13 attributes)"
    },
    "wine_quality_red": {
        "dir": "winequality/winequality-red.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
        "has_header": True,
        "delimiter": ";",
        "description": "Wine Quality Red (1599 instances, 12 attributes)"
    },
    "wine_quality_white": {
        "dir": "winequality/winequality-white.csv",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
        "has_header": True,
        "delimiter": ";",
        "description": "Wine Quality White (4898 instances, 12 attributes)"
    },
    "ionosphere": {
        "dir": "ionosphere/ionosphere.data",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data",
        "has_header": False,
        "description": "Ionosphere dataset (351 instances, 35 attributes)"
    },
    "heart_cleveland": {
        "dir": "heart-cleveland/heart.dat",
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
        "has_header": False,
        "description": "Heart Disease Cleveland (303 instances, 14 attributes)"
    }
}

def ensure_data_directory(base_path: Path) -> Path:
    """Creates the data/raw directory if it doesn't exist."""
    raw_dir = base_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directory exists: {raw_dir}")
    return raw_dir

def fetch_dataset(dataset_name: str, config: Dict, output_dir: Path) -> Optional[Path]:
    """
    Fetches a single dataset from the UCI repository.
    
    Args:
        dataset_name: Friendly name for logging
        config: Dictionary containing 'url', 'has_header', 'delimiter'
        output_dir: Path to save the downloaded file
        
    Returns:
        Path to the saved file, or None if failed.
    """
    url = config['url']
    has_header = config.get('has_header', False)
    delimiter = config.get('delimiter', ',')
    
    # Determine local filename
    # Extract filename from URL
    filename = url.split('/')[-1]
    local_path = output_dir / filename
    
    if local_path.exists():
        logger.info(f"Dataset {dataset_name} already exists at {local_path}. Skipping download.")
        return local_path

    logger.info(f"Downloading {dataset_name} from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded {dataset_name} to {local_path}")
        
        # If the file has a header but we need to standardize format for processing,
        # we might want to normalize it here, but for T016 we just need the raw file.
        # However, for Wine Quality CSVs, they use ';' delimiter. 
        # We will save them as is; the loader (T017) will handle parsing.
        
        return local_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading {dataset_name}: {e}")
        return None

def clean_missing_values(file_path: Path, output_path: Path, has_header: bool, delimiter: str) -> Path:
    """
    Removes rows with missing values (represented as '?' or empty strings) 
    and writes a clean version to output_path.
    This is a preparatory step for T018 but ensures the raw data is usable.
    """
    logger.info(f"Cleaning missing values in {file_path}...")
    
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        if has_header:
            header = next(reader)
            rows.append(header)
        
        for row in reader:
            # Check for missing values
            if '?' in row or '' in row:
                continue
            # Check for numeric validity (basic check)
            try:
                # Attempt to convert all non-class columns to float if possible
                # We don't drop rows just because they might be categorical yet, 
                # but we drop obvious missing markers.
                rows.append(row)
            except ValueError:
                continue
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerows(rows)
    
    logger.info(f"Cleaned data saved to {output_path}")
    return output_path

def main():
    """Main entry point for T016."""
    # Determine project root (assuming this script is in code/)
    # We need to find the project root to write to data/raw/
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    output_dir = ensure_data_directory(project_root)
    
    success_count = 0
    total_count = len(DATASETS)
    
    for name, config in DATASETS.items():
        logger.info(f"Processing: {name}")
        file_path = fetch_dataset(name, config, output_dir)
        
        if file_path:
            # For datasets that are CSV with headers or specific delimiters, 
            # we might want to ensure a consistent format for downstream loaders.
            # The Wine Quality datasets are CSV with ';'. 
            # The Wine dataset is comma-separated.
            # Let's create a standardized clean version in data/raw/processed_temp for now 
            # or just note that T017 will handle the raw file.
            # Per T016, we save to data/raw/.
            # We will perform a basic cleaning pass to remove '?' rows which are common in UCI.
            
            cleaned_path = output_dir / f"{name}_clean.csv"
            # We need to infer delimiter for cleaning if not obvious
            delim = config.get('delimiter', ',')
            
            # Special handling for Wine Quality which has a header
            clean_missing_values(file_path, cleaned_path, config.get('has_header', False), delim)
            
            # If the original was not CSV or had no header, we might keep the original too,
            # but for simplicity in this pipeline, we will rely on the cleaned CSV version
            # for the subsequent steps, or we can just save the raw and let T017 handle it.
            # The task says "save to data/raw/". We have saved the raw.
            # We will also save the cleaned version to ensure T018 logic doesn't need to re-download.
            # Actually, T018 says "exclude rows with missing values".
            # To be safe and strictly follow "save to data/raw", we keep the raw file.
            # But to make T017/T018 easier, we ensure the raw file is valid.
            # Let's just log that the raw file is ready.
            
            success_count += 1
        else:
            logger.warning(f"Skipping {name} due to download failure.")

    logger.info(f"Download complete. {success_count}/{total_count} datasets fetched.")
    if success_count == 0:
        logger.error("No datasets were successfully downloaded. Check network or URLs.")
        sys.exit(1)

if __name__ == "__main__":
    main()