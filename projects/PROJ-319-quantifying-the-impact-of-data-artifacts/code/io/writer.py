"""
I/O Writer module for saving artifacts and metadata.
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from astropy.io import fits
import numpy as np

from code.config import get_project_root

logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_array_checksum(array: np.ndarray) -> str:
    """Compute SHA256 checksum of a numpy array."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(array.tobytes())
    return sha256_hash.hexdigest()

def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def get_environment_info() -> Dict[str, str]:
    """Get basic environment information."""
    return {
        "python_version": sys.version,
        "platform": sys.platform,
        "cwd": os.getcwd()
    }

def save_fits_image(data: np.ndarray, header: Dict[str, Any], output_path: Path) -> None:
    """Save a numpy array and header to a FITS file."""
    hdu = fits.PrimaryHDU(data, header=header)
    hdu.writeto(output_path, overwrite=True)
    logger.info(f"Saved FITS image to {output_path}")

def save_metadata_json(data: Dict[str, Any], output_path: Path) -> None:
    """Save a dictionary to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

def generate_run_manifest() -> Dict[str, Any]:
    """Generate a run manifest with git hash, env, and config."""
    from code.config import get_config_summary
    return {
        "git_commit": get_git_commit_hash(),
        "env_vars": get_environment_info(),
        "artifact_params": get_config_summary(),
        "timestamp": subprocess.check_output(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ']).decode('ascii').strip()
    }

def write_run_manifest_for_pipeline(root: Path) -> None:
    """Write the run manifest to data/processed/run_manifest.json."""
    manifest = generate_run_manifest()
    output_path = root / "data" / "processed" / "run_manifest.json"
    save_metadata_json(manifest, output_path)

def save_run_log(log_path: Path, message: str) -> None:
    """Append a message to a run log."""
    with open(log_path, 'a') as f:
        f.write(f"{message}\n")

def write_artifact_manifest(root: Path, artifacts: List[Dict[str, str]]) -> None:
    """Write a manifest of artifacts produced."""
    output_path = root / "data" / "processed" / "artifact_manifest.json"
    save_metadata_json({"artifacts": artifacts}, output_path)