"""
Atlas management module for downloading and caching brain atlases (Schaefer/AAL).

This module handles the retrieval of parcellation atlases from GitHub releases,
ensures version pinning for reproducibility, and manages local caching to avoid
redundant downloads.
"""
import os
import logging
import hashlib
import tempfile
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urljoin

# Configuration constants
ATLAS_CACHE_DIR = Path("data/atlas_cache")
# Schaefer 2018 Atlas (400 ROIs, 7 Networks) - Version pinned for reproducibility
SCHAEFER_REPO_OWNER = "YeoLab"
SCHAEFER_REPO_NAME = "Yeo2011" # Actually YeoLab/Schaefer2018Parcellations
# Correct repo for Schaefer 2018
SCHAEFER_REPO_OWNER = "YeoLab"
SCHAEFER_REPO_NAME = "Schaefer2018Parcellations"
SCHAEFER_VERSION = "v1.1.0"
SCHAEFER_ASSET_NAME = "Schaefer2018_400Parcels_7Networks_order_FSLMNI152.nii.gz"
SCHAEFER_DOWNLOAD_URL = (
    f"https://github.com/{SCHAEFER_REPO_OWNER}/{SCHAEFER_REPO_NAME}/releases/download/"
    f"{SCHAEFER_VERSION}/{SCHAEFER_ASSET_NAME}"
)

# AAL Atlas (116 ROIs) - Alternative option
AAL_REPO_OWNER = "neurospin"
AAL_REPO_NAME = "aal"
AAL_VERSION = "v3.0"
AAL_ASSET_NAME = "aal_SPM12.zip"
AAL_DOWNLOAD_URL = (
    f"https://github.com/{AAL_REPO_OWNER}/{AAL_REPO_NAME}/releases/download/"
    f"{AAL_VERSION}/{AAL_ASSET_NAME}"
)

logger = logging.getLogger(__name__)

def _ensure_cache_dir() -> Path:
    """Ensure the atlas cache directory exists."""
    ATLAS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return ATLAS_CACHE_DIR

def _calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file for integrity verification."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> None:
    """
    Download a file from a URL with progress logging.
    
    Args:
        url: The URL to download from.
        dest_path: The destination path for the file.
        chunk_size: Size of chunks to read.
        
    Raises:
        requests.RequestException: If the download fails.
    """
    logger.info(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download complete: {dest_path.name} ({downloaded / 1024 / 1024:.2f} MB)")
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def get_atlas_path(
    atlas_type: str = "schaefer",
    force_download: bool = False
) -> Path:
    """
    Get the local path to an atlas, downloading it if necessary.
    
    Args:
        atlas_type: Either 'schaefer' (400 ROIs) or 'aal' (116 ROIs).
        force_download: If True, re-download even if cached.
        
    Returns:
        Path to the local atlas file.
        
    Raises:
        ValueError: If atlas_type is not supported.
        RuntimeError: If download fails or integrity check fails.
    """
    cache_dir = _ensure_cache_dir()
    
    if atlas_type.lower() == "schaefer":
        asset_name = SCHAEFER_ASSET_NAME
        url = SCHAEFER_DOWNLOAD_URL
        expected_hash = None # Could add hash verification if available
    elif atlas_type.lower() == "aal":
        asset_name = AAL_ASSET_NAME
        url = AAL_DOWNLOAD_URL
        expected_hash = None
    else:
        raise ValueError(f"Unsupported atlas type: {atlas_type}. Use 'schaefer' or 'aal'.")
    
    local_path = cache_dir / asset_name
    
    if local_path.exists() and not force_download:
        logger.info(f"Atlas found in cache: {local_path}")
        # Optional: Verify hash if expected_hash is defined
        return local_path
    
    logger.info(f"Atlas not found in cache or force_download=True. Downloading {asset_name}...")
    
    # Download to a temporary file first to avoid partial downloads
    with tempfile.NamedTemporaryFile(dir=cache_dir, delete=False) as tmp_file:
        temp_path = Path(tmp_file.name)
    
    try:
        download_file(url, temp_path)
        
        # Move temp file to final location
        if local_path.exists():
            local_path.unlink()
        temp_path.rename(local_path)
        
        logger.info(f"Atlas successfully downloaded and cached: {local_path}")
        return local_path
        
    except Exception as e:
        # Clean up temp file on failure
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to download atlas: {e}")
        raise RuntimeError(f"Atlas download failed: {e}") from e

def load_atlas_labels(atlas_path: Path) -> Dict[int, str]:
    """
    Load ROI labels from an atlas file.
    
    Note: This is a simplified implementation. In a full pipeline, this would
    parse the specific label file associated with the atlas (e.g., 
    Schaefer2018_400Parcels_7Networks_order.txt).
    
    Args:
        atlas_path: Path to the atlas NIfTI file.
        
    Returns:
        Dictionary mapping ROI index to label string.
    """
    # Placeholder for label loading logic
    # In a real scenario, we would parse the corresponding .txt file
    # For now, we return a generic mapping
    import numpy as np
    import nibabel as nib
    
    img = nib.load(atlas_path)
    data = img.get_fdata()
    unique_labels = np.unique(data)
    unique_labels = unique_labels[unique_labels != 0] # Exclude background
    
    labels = {}
    for i, label in enumerate(unique_labels):
        labels[int(label)] = f"ROI_{int(label)}"
        
    return labels

def main():
    """Main entry point for downloading and verifying atlases."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Download Schaefer 400
        schaefer_path = get_atlas_path("schaefer")
        print(f"Schaefer Atlas: {schaefer_path}")
        
        # Download AAL
        aal_path = get_atlas_path("aal")
        print(f"AAL Atlas: {aal_path}")
        
        # Verify loading
        schaefer_labels = load_atlas_labels(schaefer_path)
        print(f"Schaefer loaded {len(schaefer_labels)} ROIs.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())