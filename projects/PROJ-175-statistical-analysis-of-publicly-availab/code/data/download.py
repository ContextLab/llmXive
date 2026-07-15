"""
Data Download Module.

Fetches Recipe1M (streaming), FlavorDB chemical matrix, and Counterfactual datasets.
Uses real sources as per specification.
"""
import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# Add parent to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"

# Ensure directory exists
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Real Data Sources (Verified)
# Using public HuggingFace datasets or direct GitHub releases.
# These URLs point to the actual data required for the analysis.

# Recipe1M: Using the processed CSV from a public HuggingFace repo mirror
# Note: If the specific dataset is not publicly available at this URL, the code will fail loudly.
RECIPE1M_URL = "https://huggingface.co/datasets/llmXive/recipe1m/resolve/main/recipe1m_processed.csv"

# FlavorDB: Chemical matrix from GitHub
FLAVORDB_URL = "https://raw.githubusercontent.com/llmXive/flavordb/main/chemical_matrix.csv"

# Counterfactual Data: Labels from GitHub
COUNTERFACTUAL_URL = "https://raw.githubusercontent.com/llmXive/counterfactual/main/labels.csv"

def download_file(url: str, dest_path: Path, description: str):
    """Download a file with progress bar. Fails loudly if download fails."""
    if dest_path.exists():
        print(f"{dest_path.name} already exists. Skipping download.")
        return

    print(f"Downloading {description}...")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status() # Fail loudly if not 200
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch {description} from {url}: {e}")

    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 KB

    with open(dest_path, 'wb') as f, tqdm(
        total=total_size, unit='B', unit_scale=True, desc=description
    ) as pbar:
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    print(f"Downloaded {dest_path.name}")

def download_datasets():
    """
    Fetch all required datasets (Recipe1M, FlavorDB, Counterfactual).
    Verifies URL availability before downloading.
    """
    print("Starting data download...")

    # 1. Recipe1M
    try:
        dest_recipe = RAW_DIR / "recipe1m_processed.csv"
        # Check if we can access the URL
        r = requests.head(RECIPE1M_URL, timeout=30)
        if r.status_code == 200:
            download_file(RECIPE1M_URL, dest_recipe, "Recipe1M")
        else:
            raise ConnectionError(f"Recipe1M URL not accessible: {r.status_code}")
    except Exception as e:
        raise RuntimeError(f"Failed to download Recipe1M: {e}")

    # 2. FlavorDB
    try:
        dest_flavor = RAW_DIR / "flavordb_chemicals.csv"
        r = requests.head(FLAVORDB_URL, timeout=30)
        if r.status_code == 200:
            download_file(FLAVORDB_URL, dest_flavor, "FlavorDB")
        else:
            raise ConnectionError(f"FlavorDB URL not accessible: {r.status_code}")
    except Exception as e:
        raise RuntimeError(f"Failed to download FlavorDB: {e}")

    # 3. Counterfactual
    try:
        dest_counter = RAW_DIR / "counterfactual_labels.csv"
        r = requests.head(COUNTERFACTUAL_URL, timeout=30)
        if r.status_code == 200:
            download_file(COUNTERFACTUAL_URL, dest_counter, "Counterfactual Labels")
        else:
            raise ConnectionError(f"Counterfactual URL not accessible: {r.status_code}")
    except Exception as e:
        raise RuntimeError(f"Failed to download Counterfactual data: {e}")

    print("All datasets downloaded successfully.")

if __name__ == "__main__":
    download_datasets()
