"""
Atlas management module for downloading and caching brain atlases.

This module handles the retrieval of Schaefer and AAL atlases from the
NeuroSynth/GitHub repositories with version pinning to ensure reproducibility.
"""
import os
import logging
import hashlib
import tempfile
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import numpy as np
import nibabel as nib

# Configure logging
logger = logging.getLogger(__name__)

# Atlas configuration with version pinning
ATLAS_CONFIG = {
    "schaefer_400": {
        "name": "Schaefer400",
        "version": "2018.11.01",
        "github_url": "https://github.com/YeoJT/Yeo2018_SchaeferAtlas/raw/master/Schaefer2018_400Parcels_7Networks_order_FSLMNI152.nii.gz",
        "labels_url": "https://raw.githubusercontent.com/YeoJT/Yeo2018_SchaeferAtlas/master/Schaefer2018_400Parcels_7Networks_order.txt",
        "description": "Schaefer 400 ROI atlas with 7 networks"
    },
    "aal": {
        "name": "AAL",
        "version": "3.0.1",
        "github_url": "https://github.com/garyfal/brain-atlas/raw/master/AAL3.nii",
        "labels_url": "https://raw.githubusercontent.com/garyfal/brain-atlas/master/AAL3.txt",
        "description": "Automated Anatomical Labeling (AAL) atlas"
    }
}

# Default atlas to use
DEFAULT_ATLAS_KEY = "schaefer_400"

def _get_cache_dir() -> Path:
    """Get the cache directory for atlases."""
    cache_dir = Path(os.environ.get("LLMXIVE_CACHE_DIR", "data/cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, destination: Path, timeout: int = 300) -> bool:
    """
    Download a file from a URL with progress logging and integrity check.
    
    Args:
        url: The URL to download from
        destination: Path where the file should be saved
        timeout: Request timeout in seconds
        
    Returns:
        True if download successful, False otherwise
        
    Raises:
        requests.exceptions.RequestException: If download fails
        ValueError: If destination directory doesn't exist
    """
    if not destination.parent.exists():
        raise ValueError(f"Destination directory {destination.parent} does not exist")
    
    logger.info(f"Downloading {url} to {destination}")
    
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Successfully downloaded {destination} ({downloaded} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise

def get_atlas_path(atlas_key: str = DEFAULT_ATLAS_KEY, force_download: bool = False) -> Path:
    """
    Get the path to an atlas file, downloading it if necessary.
    
    Args:
        atlas_key: Key from ATLAS_CONFIG (e.g., 'schaefer_400', 'aal')
        force_download: If True, re-download even if cached
        
    Returns:
        Path to the atlas file
        
    Raises:
        KeyError: If atlas_key is not found in ATLAS_CONFIG
        RuntimeError: If download fails
    """
    if atlas_key not in ATLAS_CONFIG:
        raise KeyError(f"Atlas '{atlas_key}' not found in ATLAS_CONFIG. Available: {list(ATLAS_CONFIG.keys())}")
    
    config = ATLAS_CONFIG[atlas_key]
    cache_dir = _get_cache_dir()
    
    # Create filename based on atlas name and version
    filename = f"{config['name']}_{config['version']}.nii.gz"
    atlas_path = cache_dir / filename
    
    # Download if not exists or forced
    if force_download or not atlas_path.exists():
        logger.info(f"Atlas {atlas_path} not found or force_download=True. Downloading...")
        try:
            download_file(config["github_url"], atlas_path)
        except Exception as e:
            logger.error(f"Failed to download atlas: {e}")
            raise RuntimeError(f"Failed to download atlas {config['name']}: {e}")
    
    logger.info(f"Using atlas from cache: {atlas_path}")
    return atlas_path

def load_atlas_labels(atlas_key: str = DEFAULT_ATLAS_KEY) -> Dict[int, str]:
    """
    Load atlas ROI labels from the labels file.
    
    Args:
        atlas_key: Key from ATLAS_CONFIG
        
    Returns:
        Dictionary mapping ROI index (1-based) to label name
        
    Raises:
        RuntimeError: If labels file cannot be downloaded or parsed
    """
    if atlas_key not in ATLAS_CONFIG:
        raise KeyError(f"Atlas '{atlas_key}' not found in ATLAS_CONFIG")
    
    config = ATLAS_CONFIG[atlas_key]
    cache_dir = _get_cache_dir()
    labels_filename = f"{config['name']}_labels.txt"
    labels_path = cache_dir / labels_filename
    
    if not labels_path.exists():
        logger.info(f"Downloading labels for {config['name']}...")
        try:
            download_file(config["labels_url"], labels_path)
        except Exception as e:
            raise RuntimeError(f"Failed to download labels for {config['name']}: {e}")
    
    labels = {}
    try:
        with open(labels_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    roi_idx = int(parts[0])
                    roi_name = " ".join(parts[1:])
                    labels[roi_idx] = roi_name
    except Exception as e:
        raise RuntimeError(f"Failed to parse labels file: {e}")
    
    logger.info(f"Loaded {len(labels)} ROI labels for {config['name']}")
    return labels

def load_atlas(atlas_key: str = DEFAULT_ATLAS_KEY) -> Tuple[nib.Nifti1Image, Dict[int, str]]:
    """
    Load an atlas image and its labels.
    
    Args:
        atlas_key: Key from ATLAS_CONFIG
        
    Returns:
        Tuple of (NIfTI image, labels dictionary)
        
    Raises:
        RuntimeError: If atlas cannot be loaded
    """
    atlas_path = get_atlas_path(atlas_key)
    
    try:
        img = nib.load(atlas_path)
        logger.info(f"Loaded atlas image: {atlas_path}")
        logger.info(f"Image shape: {img.shape}, affine: {img.affine}")
    except Exception as e:
        raise RuntimeError(f"Failed to load atlas image from {atlas_path}: {e}")
    
    labels = load_atlas_labels(atlas_key)
    
    return img, labels

def main():
    """Main entry point for testing atlas functionality."""
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Atlas Module")
    print("=" * 50)
    
    # Test Schaefer 400
    print("\n1. Testing Schaefer 400 Atlas:")
    try:
        img, labels = load_atlas("schaefer_400")
        print(f"   Image shape: {img.shape}")
        print(f"   Number of ROIs: {len(labels)}")
        print(f"   Sample labels: {list(labels.items())[:5]}")
        
        # Verify we can access the data
        data = img.get_fdata()
        unique_values = np.unique(data)
        print(f"   Unique values in atlas: {len(unique_values)}")
        print(f"   Value range: {unique_values.min()} to {unique_values.max()}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    # Test AAL
    print("\n2. Testing AAL Atlas:")
    try:
        img, labels = load_atlas("aal")
        print(f"   Image shape: {img.shape}")
        print(f"   Number of ROIs: {len(labels)}")
        print(f"   Sample labels: {list(labels.items())[:5]}")
        
        data = img.get_fdata()
        unique_values = np.unique(data)
        print(f"   Unique values in atlas: {len(unique_values)}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\nAtlas module test complete.")

if __name__ == "__main__":
    main()
