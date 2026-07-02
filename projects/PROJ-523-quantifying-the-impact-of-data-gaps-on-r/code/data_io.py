"""
Data I/O utilities for HEALPix maps, masks, and metadata.

Handles loading/saving of .fits files and JSON metadata with checksums.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
import healpy as hp

from config import PROJECT_ROOT, DATA_DERIVED_DIR, DATA_METADATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_array_checksum(arr: np.ndarray) -> str:
    """Compute SHA256 checksum of a numpy array."""
    # Convert to bytes in a consistent way
    data_bytes = arr.tobytes()
    return hashlib.sha256(data_bytes).hexdigest()


def save_map_to_fits(map_data: np.ndarray, output_path: Union[str, Path], overwrite: bool = True) -> str:
    """Save a HEALPix map to a .fits file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    hp.write_map(str(output_path), map_data, overwrite=overwrite)
    logger.info(f"Saved map to {output_path}")
    return str(output_path)


def load_map_from_fits(file_path: Union[str, Path], field: int = 0) -> np.ndarray:
    """Load a HEALPix map from a .fits file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Map file not found: {file_path}")

    # hp.read_map returns a tuple if multiple fields, or array if single
    # We assume single temperature map or specific field index
    data = hp.read_map(str(file_path), field=field, nest=True)
    logger.info(f"Loaded map from {file_path}, shape: {data.shape}")
    return data


def save_mask_to_fits(mask_data: np.ndarray, output_path: Union[str, Path], overwrite: bool = True) -> str:
    """Save a HEALPix mask to a .fits file."""
    # Masks are typically boolean or 0/1 integers
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure data is float for healpy or keep as is? Healpy handles various types.
    hp.write_map(str(output_path), mask_data, overwrite=overwrite)
    logger.info(f"Saved mask to {output_path}")
    return str(output_path)


def load_mask_from_fits(file_path: Union[str, Path]) -> np.ndarray:
    """Load a HEALPix mask from a .fits file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Mask file not found: {file_path}")

    mask = hp.read_map(str(file_path), nest=True)
    logger.info(f"Loaded mask from {file_path}, shape: {mask.shape}")
    return mask


def save_metadata(metadata: Dict[str, Any], output_path: Union[str, Path]) -> str:
    """Save metadata dictionary to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved metadata to {output_path}")
    return str(output_path)


def load_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load metadata from a JSON file."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    logger.info(f"Loaded metadata from {file_path}")
    return data


def save_realization(
    map_data: np.ndarray,
    mask_data: Optional[np.ndarray] = None,
    metadata: Optional[Dict[str, Any]] = None,
    realization_id: str = "unknown",
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Save a complete realization (map, optional mask, metadata) to disk.

    Returns a dictionary of paths to saved files.
    """
    if output_dir is None:
        output_dir = Path(DATA_DERIVED_DIR)

    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {}

    # Save Map
    map_path = output_dir / f"{realization_id}_map.fits"
    save_map_to_fits(map_data, map_path)
    paths["map"] = str(map_path)

    # Save Mask if provided
    if mask_data is not None:
        mask_path = output_dir / f"{realization_id}_mask.fits"
        save_mask_to_fits(mask_data, mask_path)
        paths["mask"] = str(mask_path)

    # Save Metadata if provided
    if metadata is not None:
        meta_path = output_dir / f"{realization_id}_meta.json"
        # Add checksums to metadata before saving
        if "map_checksum" not in metadata:
            metadata["map_checksum"] = compute_array_checksum(map_data)
        if mask_data is not None and "mask_checksum" not in metadata:
            metadata["mask_checksum"] = compute_array_checksum(mask_data)

        save_metadata(metadata, meta_path)
        paths["metadata"] = str(meta_path)

    return paths


def load_realization(
    realization_id: str,
    load_mask: bool = True,
    load_metadata: bool = True,
    input_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load a complete realization from disk.

    Returns a dictionary with 'map', 'mask' (optional), 'metadata' (optional).
    """
    if input_dir is None:
        input_dir = Path(DATA_DERIVED_DIR)

    result = {}

    map_path = input_dir / f"{realization_id}_map.fits"
    if map_path.exists():
        result["map"] = load_map_from_fits(map_path)
    else:
        logger.warning(f"Map file not found for {realization_id}: {map_path}")

    if load_mask:
        mask_path = input_dir / f"{realization_id}_mask.fits"
        if mask_path.exists():
            result["mask"] = load_mask_from_fits(mask_path)
        else:
            logger.warning(f"Mask file not found for {realization_id}: {mask_path}")

    if load_metadata:
        meta_path = input_dir / f"{realization_id}_meta.json"
        if meta_path.exists():
            result["metadata"] = load_metadata(meta_path)
        else:
            logger.warning(f"Metadata file not found for {realization_id}: {meta_path}")

    return result
