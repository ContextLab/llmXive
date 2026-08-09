import os
import logging
import hashlib
import tempfile
import requests
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import nibabel as nib

import src.config as config

logger = logging.getLogger(__name__)

# Atlas URLs (GitHub raw content for versioned releases)
# Using Schaefer 2018 400 parcellation as default
ATLAS_URL = "https://raw.githubusercontent.com/YeoLab/Yeo2011_Extended/refs/heads/master/Atlases/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_1mm.nii.gz"
ATLAS_LABELS_URL = "https://raw.githubusercontent.com/YeoLab/Yeo2011_Extended/refs/heads/master/Atlases/Schaefer2018_400Parcels_7Networks_order.txt"
ATLAS_CACHE_DIR = config.PROJECT_ROOT / "data" / "atlas_cache"
ATLAS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest_path: Path) -> None:
    """
    Download a file from a URL with progress logging.
    
    Args:
        url: URL to download from.
        dest_path: Local path to save the file.
        
    Raises:
        requests.RequestException: If download fails.
    """
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Downloaded {dest_path.name} successfully")
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise


def get_atlas_path(atlas_type: str = "schaefer_400") -> Path:
    """
    Get the path to the atlas file, downloading if necessary.
    
    Args:
        atlas_type: Type of atlas (currently only 'schaefer_400' supported).
        
    Returns:
        Path to the atlas NIfTI file.
        
    Raises:
        ValueError: If atlas_type is not supported.
    """
    if atlas_type != "schaefer_400":
        raise ValueError(f"Unsupported atlas type: {atlas_type}")
        
    atlas_file = ATLAS_CACHE_DIR / "Schaefer2018_400Parcels.nii.gz"
    
    if not atlas_file.exists():
        download_file(ATLAS_URL, atlas_file)
        
    return atlas_file


def load_atlas_labels(labels_path: Optional[Path] = None) -> list:
    """
    Load atlas labels from a text file.
    
    Args:
        labels_path: Path to the labels file. If None, uses default URL.
        
    Returns:
        List of label strings.
    """
    if labels_path is None:
        labels_path = ATLAS_CACHE_DIR / "labels.txt"
        if not labels_path.exists():
            download_file(ATLAS_LABELS_URL, labels_path)
            
    labels = []
    with open(labels_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                labels.append(line.strip())
                
    return labels


def load_atlas(atlas_type: str = "schaefer_400") -> Tuple[nib.Nifti1Image, list]:
    """
    Load the atlas image and labels.
    
    Args:
        atlas_type: Type of atlas to load.
        
    Returns:
        Tuple of (nibabel image object, list of labels).
    """
    atlas_path = get_atlas_path(atlas_type)
    atlas_img = nib.load(atlas_path)
    labels = load_atlas_labels()
    
    return atlas_img, labels


def main():
    """Main entry point for atlas download script."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Downloading and caching atlas...")
    atlas_path = get_atlas_path()
    logger.info(f"Atlas downloaded to: {atlas_path}")
    
    # Verify loading
    img, labels = load_atlas()
    logger.info(f"Atlas shape: {img.shape}")
    logger.info(f"Number of labels: {len(labels)}")
    logger.info(f"First 5 labels: {labels[:5]}")


if __name__ == "__main__":
    main()