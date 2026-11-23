"""
Atlas management module for downloading and caching brain atlases.

This module provides functionality to download the Schaefer‑400 and AAL‑200
atlases, cache them under ``data/atlas/`` and load both the NIfTI image and
a DataFrame of ROI labels.

Public API:
  - download_file(url, destination, timeout=300) -> bool
  - get_atlas_path(atlas_key=DEFAULT_ATLAS_KEY, force_download=False) -> Path
  - load_atlas_labels(name: str = DEFAULT_ATLAS_KEY) -> Dict[int, str]
  - load_atlas(name: str = DEFAULT_ATLAS_KEY) -> Tuple[nib.Nifti1Image, pd.DataFrame]
"""
import os
import logging
import hashlib
import requests
from pathlib import Path
from typing import Tuple, Dict

import nibabel as nib
import pandas as pd
from llmxive_toolkit import paths

# Configure module logger
logger = logging.getLogger(__name__)

# Atlas configuration with version‑pinned URLs
ATLAS_CONFIG = {
    "schaefer_400": {
        "name": "Schaefer400",
        "version": "2018.11.01",
        "nii_url": "https://github.com/YeoJT/Yeo2018_SchaeferAtlas/raw/master/Schaefer2018_400Parcels_7Networks_order_FSLMNI152.nii.gz",
        "labels_url": "https://raw.githubusercontent.com/YeoJT/Yeo2018_SchaeferAtlas/master/Schaefer2018_400Parcels_7Networks_order.txt",
        "description": "Schaefer 400 ROI atlas with 7 networks"
    },
    "aal": {
        "name": "AAL200",
        "version": "3.0.1",
        "nii_url": "https://github.com/garyfal/brain-atlas/raw/master/AAL3.nii",
        "labels_url": "https://raw.githubusercontent.com/garyfal/brain-atlas/master/AAL3.txt",
        "description": "Automated Anatomical Labeling (AAL) atlas (200 ROIs)"
    }
}

# Default atlas identifier (matches the key in ATLAS_CONFIG)
DEFAULT_ATLAS_KEY = "schaefer_400"


def _get_cache_dir() -> Path:
    """
    Return the directory used for caching atlas files.

    The cache lives under ``data/atlas/`` (created via
    ``llmxive_toolkit.paths.ensure_dir``). Tests patch this function,
    so the implementation must be a single call that can be overridden.
    """
    cache_dir = paths.data("atlas")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _calculate_file_hash(file_path: Path) -> str:
    """Calculate the SHA256 hash of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()


def download_file(url: str, destination: Path, timeout: int = 300) -> bool:
    """
    Download a file from ``url`` to ``destination`` with progress logging.

    Parameters
    ----------
    url: str
        URL of the file to download.
    destination: Path
        Full path (including filename) where the file will be saved.
    timeout: int, optional
        Request timeout in seconds (default: 300).

    Returns
    -------
    bool
        ``True`` if the download succeeds; raises on failure.

    Raises
    ------
    requests.exceptions.RequestException
        If the HTTP request fails.
    ValueError
        If the parent directory of ``destination`` does not exist.
    """
    if not destination.parent.exists():
        raise ValueError(f"Destination directory {destination.parent} does not exist")

    logger.info(f"Downloading {url} → {destination}")

    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = (downloaded / total) * 100
                        logger.debug(f"Download progress: {pct:.1f}%")

        logger.info(f"Finished downloading {destination} ({downloaded} bytes)")
        return True

    except requests.exceptions.RequestException as exc:
        logger.error(f"Error downloading {url}: {exc}")
        raise


def get_atlas_path(atlas_key: str = DEFAULT_ATLAS_KEY, force_download: bool = False) -> Path:
    """
    Return the cached path of the atlas NIfTI file, downloading it if necessary.

    Parameters
    ----------
    atlas_key: str
        Key from ``ATLAS_CONFIG`` (e.g., ``'schaefer_400'`` or ``'aal'``).
    force_download: bool, optional
        Re‑download even if a cached file exists.

    Returns
    -------
    Path
        Path to the cached ``.nii.gz`` file.

    Raises
    ------
    KeyError
        If ``atlas_key`` is unknown.
    RuntimeError
        If the download fails.
    """
    if atlas_key not in ATLAS_CONFIG:
        raise KeyError(
            f"Atlas '{atlas_key}' not found. Available keys: {list(ATLAS_CONFIG)}"
        )

    cfg = ATLAS_CONFIG[atlas_key]
    cache_dir = _get_cache_dir()
    filename = f"{cfg['name']}_{cfg['version']}.nii.gz"
    atlas_path = cache_dir / filename

    if force_download or not atlas_path.exists():
        logger.info(f"Atlas file not present (or force_download=True). Downloading {cfg['name']}...")
        try:
            download_file(cfg["nii_url"], atlas_path)
        except Exception as exc:
            raise RuntimeError(f"Failed to download atlas {cfg['name']}: {exc}")

    logger.debug(f"Using cached atlas at {atlas_path}")
    return atlas_path


def _resolve_name_to_key(name: str) -> str:
    """
    Helper to map a user‑friendly name (e.g., ``'Schaefer400'``) to the
    internal ``ATLAS_CONFIG`` key.

    The mapping is case‑insensitive and accepts the exact keys used in
    ``ATLAS_CONFIG``.
    """
    lowered = name.lower()
    if lowered in ATLAS_CONFIG:
        return lowered
    if "schaefer" in lowered:
        return "schaefer_400"
    if "aal" in lowered:
        return "aal"
    raise KeyError(f"Unrecognised atlas name '{name}'. Valid names: {list(ATLAS_CONFIG)}")


def load_atlas_labels(name: str = DEFAULT_ATLAS_KEY) -> Dict[int, str]:
    """
    Load ROI label mappings for the requested atlas.

    Parameters
    ----------
    name: str
        Atlas identifier (e.g., ``'Schaefer400'`` or ``'AAL200'``).

    Returns
    -------
    dict[int, str]
        Mapping from ROI index (1‑based) to label string.

    Raises
    ------
    RuntimeError
        If the label file cannot be downloaded or parsed.
    """
    key = _resolve_name_to_key(name)
    cfg = ATLAS_CONFIG[key]
    cache_dir = _get_cache_dir()
    labels_file = cache_dir / f"{cfg['name']}_labels.txt"

    if not labels_file.exists():
        logger.info(f"Downloading label file for {cfg['name']}...")
        try:
            download_file(cfg["labels_url"], labels_file)
        except Exception as exc:
            raise RuntimeError(f"Failed to download labels for {cfg['name']}: {exc}")

    labels: Dict[int, str] = {}
    try:
        with open(labels_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    idx = int(parts[0])
                    label = " ".join(parts[1:])
                    labels[idx] = label
    except Exception as exc:
        raise RuntimeError(f"Error parsing label file {labels_file}: {exc}")

    logger.debug(f"Loaded {len(labels)} labels for {cfg['name']}")
    return labels


def load_atlas(name: str = DEFAULT_ATLAS_KEY) -> Tuple[nib.Nifti1Image, pd.DataFrame]:
    """
    Load the atlas NIfTI image and a DataFrame of ROI labels.

    Parameters
    ----------
    name: str
        Atlas identifier (e.g., ``'Schaefer400'`` or ``'AAL200'``).

    Returns
    -------
    tuple
        ``(nib.Nifti1Image, pandas.DataFrame)`` where the DataFrame has
        columns ``['ROI', 'Label']``.

    Raises
    ------
    RuntimeError
        If the image cannot be loaded.
    """
    key = _resolve_name_to_key(name)

    # Load the image
    atlas_path = get_atlas_path(key)
    try:
        img = nib.load(atlas_path)
        logger.info(f"Loaded atlas image from {atlas_path} (shape={img.shape})")
    except Exception as exc:
        raise RuntimeError(f"Failed to load NIfTI image for atlas {key}: {exc}")

    # Load labels (dictionary) and convert to DataFrame
    label_dict = load_atlas_labels(key)
    df = pd.DataFrame(
        [(roi, label) for roi, label in sorted(label_dict.items())],
        columns=["ROI", "Label"]
    )
    return img, df


def main() -> None:
    """Simple sanity‑check entry point used during development."""
    logging.basicConfig(level=logging.INFO)
    print("Atlas module sanity check")
    for test_name in ["schaefer_400", "aal", "Schaefer400", "AAL200"]:
        try:
            img, df = load_atlas(test_name)
            print(f"{test_name}: image shape={img.shape}, ROIs={len(df)}")
        except Exception as e:
            print(f"{test_name}: ERROR -> {e}")


if __name__ == "__main__":
    main()