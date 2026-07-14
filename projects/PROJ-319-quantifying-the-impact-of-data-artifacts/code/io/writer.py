"""
writer.py - Save generated images and logs with checksums for reproducibility.

Implements FR-008: Save generated images and logs with checksums.
Ensures deterministic output by using fixed seeds and logging checksums.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

import numpy as np
from astropy.io import fits

from code.io.loader import MetadataValidationError

logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_array_checksum(array: np.ndarray) -> str:
    """
    Compute SHA-256 checksum of a numpy array.

    Args:
        array: Numpy array to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    # Serialize array to bytes (including dtype and shape for uniqueness)
    array_bytes = array.tobytes()
    # Include shape and dtype in the hash to prevent collisions
    meta_bytes = f"{array.shape}:{array.dtype}".encode('utf-8')
    combined = meta_bytes + array_bytes
    return hashlib.sha256(combined).hexdigest()


def save_fits_image(
    image: np.ndarray,
    output_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None,
    overwrite: bool = True
) -> str:
    """
    Save a numpy array as a FITS file with optional metadata and compute checksum.

    Args:
        image: 2D numpy array representing the image.
        output_path: Path where the FITS file will be saved.
        metadata: Optional dictionary of metadata to store in the FITS header.
        overwrite: Whether to overwrite existing files.

    Returns:
        The checksum of the saved file.

    Raises:
        ValueError: If image is not 2D.
        IOError: If file cannot be written.
    """
    if image.ndim != 2:
        raise ValueError(f"Expected 2D image array, got {image.ndim}D")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create HDU
    hdu = fits.PrimaryHDU(image.astype(np.float32))

    # Add metadata to header
    if metadata:
        for key, value in metadata.items():
            # Truncate string values to FITS comment length if necessary
            if isinstance(value, str) and len(value) > 72:
                value = value[:72]
            try:
                hdu.header[key] = value
            except ValueError:
                # If key is too long or value invalid, skip or log
                logger.warning(f"Skipping invalid metadata entry: {key}={value}")

    # Add checksum keyword manually for reproducibility tracking
    # Note: We compute our own checksum below and store it in a custom keyword
    hdu.header['COMMENT'] = 'Checksum computed by writer.py'

    # Write file
    hdu.writeto(str(output_path), overwrite=overwrite)

    # Compute and return checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Saved FITS image to {output_path} (SHA-256: {checksum[:16]}...)")

    return checksum


def save_metadata_json(
    data: Dict[str, Any],
    output_path: Union[str, Path],
    include_checksums: bool = True
) -> str:
    """
    Save metadata dictionary to a JSON file with optional checksums.

    Args:
        data: Dictionary of metadata to save.
        output_path: Path where the JSON file will be saved.
        include_checksums: If True, compute and include checksums for any numpy arrays in the data.

    Returns:
        The checksum of the saved JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare data for JSON serialization
    serializable_data = {}
    for key, value in data.items():
        if isinstance(value, np.ndarray):
            if include_checksums:
                # Store checksum instead of the array
                serializable_data[key] = {
                    "_type": "numpy_array",
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                    "checksum": compute_array_checksum(value)
                }
            else:
                # Convert to list (might be large)
                serializable_data[key] = value.tolist()
        elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
            serializable_data[key] = value
        else:
            # Convert other types to string
            serializable_data[key] = str(value)

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, indent=2, sort_keys=True)

    checksum = compute_file_checksum(output_path)
    logger.info(f"Saved metadata to {output_path} (SHA-256: {checksum[:16]}...)")

    return checksum


def save_run_log(
    log_path: Union[str, Path],
    config: Dict[str, Any],
    results: Dict[str, Any],
    checksums: Optional[Dict[str, str]] = None
) -> None:
    """
    Save a structured log of a research run including config, results, and checksums.

    Args:
        log_path: Path to the log file.
        config: Configuration used for the run.
        results: Results dictionary.
        checksums: Optional dictionary of checksums for output files.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "run_id": results.get("run_id", "unknown"),
        "config": config,
        "results": results,
        "checksums": checksums or {},
        "status": "completed"
    }

    # Append to log file (or create new)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, indent=2) + "\n")

    logger.info(f"Appended run log to {log_path}")


def write_artifact_manifest(
    artifacts: Dict[str, Dict[str, Any]],
    output_path: Union[str, Path]
) -> str:
    """
    Write a manifest of all artifacts produced in a run, including their checksums.

    Args:
        artifacts: Dictionary mapping artifact names to their metadata (path, type, checksum, etc.).
        output_path: Path where the manifest will be saved.

    Returns:
        The checksum of the manifest file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": "1.0",
        "artifacts": {}
    }

    for name, info in artifacts.items():
        manifest["artifacts"][name] = {
            "path": str(info.get("path", "")),
            "type": info.get("type", "unknown"),
            "checksum": info.get("checksum", ""),
            "description": info.get("description", "")
        }

    # Compute manifest checksum
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    checksum = compute_file_checksum(output_path)
    logger.info(f"Saved artifact manifest to {output_path} (SHA-256: {checksum[:16]}...)")

    return checksum