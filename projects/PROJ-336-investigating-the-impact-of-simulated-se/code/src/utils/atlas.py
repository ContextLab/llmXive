import os
import logging
import hashlib
import tempfile
import requests
from pathlib import Path

# Define the URL for the Schaefer AAL atlas (400 ROIs) on GitHub
ATLAS_URL = "https://raw.githubusercontent.com/ThomasYeoLab/HumanBrainProjectAtlas/master/ParcellationMaps/Schaefer2018LR_400CortSurf_mask.npy"
ATLAS_FILENAME = "Schaefer2018LR_400CortSurf_mask.npy"

def download_file(url, filepath):
    """Downloads a file from the given URL to the specified filepath."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded {url} to {filepath}")
        return filepath
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading file from {url}: {e}")
        return None

def get_atlas_path(cache_dir):
    """Returns the path to the cached atlas file."""
    filepath = Path(cache_dir) / ATLAS_FILENAME
    if not filepath.exists():
        os.makedirs(cache_dir, exist_ok=True)  # Ensure cache directory exists
        download_file(ATLAS_URL, filepath)
    return filepath

def load_atlas_labels(filepath):
    """Loads the atlas labels from the given file."""
    import numpy as np
    try:
        atlas = np.load(filepath)
        logging.info(f"Loaded atlas from {filepath}")
        return atlas
    except Exception as e:
        logging.error(f"Error loading atlas from {filepath}: {e}")
        return None

def main():
    """Main function to download and load the atlas."""
    cache_dir = Path("data") / "atlas_cache"  # Create a cache directory within data/
    atlas_path = get_atlas_path(cache_dir)
    if atlas_path:
        labels = load_atlas_labels(atlas_path)
        if labels is not None:
            logging.info("Atlas loaded successfully.")
            # You can now use the 'labels' array for your analysis
        else:
            logging.error("Failed to load atlas labels.")
    else:
        logging.error("Failed to download or find atlas file.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    main()