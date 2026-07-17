import hashlib
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

import numpy as np

logger = logging.getLogger(__name__)

def get_git_commit_hash() -> Optional[str]:
    """
    Attempt to retrieve the current git commit hash.
    Returns None if git is not available or not in a repository.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.warning("Could not retrieve git commit hash. Proceeding without it.")
        return None

def get_environment_info() -> Dict[str, Any]:
    """
    Gather basic environment information relevant to reproducibility.
    """
    env_vars = {
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "HOSTNAME": os.environ.get("HOSTNAME", "unknown"),
    }
    # Filter out potentially sensitive or overly large env vars if needed
    return env_vars

def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_array_checksum(array: np.ndarray) -> str:
    """
    Compute SHA-256 checksum of a numpy array's raw data.
    """
    sha256_hash = hashlib.sha256()
    sha256_hash.update(array.tobytes())
    return sha256_hash.hexdigest()

def save_fits_image(
    data: np.ndarray, 
    header: Dict[str, Any], 
    output_path: Union[str, Path]
) -> str:
    """
    Save a numpy array as a FITS image with the provided header metadata.
    Returns the checksum of the saved file.
    """
    try:
        from astropy.io import fits
    except ImportError:
        raise ImportError("astropy is required to save FITS files. Install it via pip.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    hdu = fits.PrimaryHDU(data)
    for key, value in header.items():
        hdu.header[key] = value
    
    hdu.writeto(path, overwrite=True)
    return compute_file_checksum(path)

def save_metadata_json(metadata: Dict[str, Any], output_path: Union[str, Path]) -> str:
    """
    Save metadata dictionary to a JSON file.
    Returns the checksum of the saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    return compute_file_checksum(path)

def save_run_log(
    log_entries: List[Dict[str, Any]], 
    output_path: Union[str, Path]
) -> str:
    """
    Save a list of log entry dictionaries to a JSON log file.
    Returns the checksum of the saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_entries, f, indent=2, default=str)
    
    return compute_file_checksum(path)

def write_artifact_manifest(
    artifacts: List[Dict[str, Any]], 
    output_path: Union[str, Path]
) -> str:
    """
    Write a manifest of artifacts (files generated in this run) to a JSON file.
    Each artifact dict should contain: path, checksum, type, description.
    Returns the checksum of the manifest file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(artifacts, f, indent=2, default=str)
    
    return compute_file_checksum(path)

def generate_run_manifest(
    artifact_params: Dict[str, Any],
    output_path: Union[str, Path] = "data/processed/run_manifest.json"
) -> str:
    """
    Generate and save a comprehensive run manifest for reproducibility audit trail.
    This includes:
    - Git commit hash
    - Environment variables
    - Timestamp
    - Full artifact parameter set used for the run
    
    Args:
        artifact_params: Dictionary containing all parameters used for this run
        output_path: Path to save the manifest JSON file
    
    Returns:
        Checksum of the generated manifest file
    """
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_commit": get_git_commit_hash(),
        "environment": get_environment_info(),
        "artifact_parameters": artifact_params,
        "schema_version": "1.0"
    }
    
    return save_metadata_json(manifest, output_path)