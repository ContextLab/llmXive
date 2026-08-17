"""
IO Writer module: Saves images, metadata, and manifests.
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from astropy.io import fits
from code.config import get_project_root

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception:
        return "unknown"

def get_environment_info() -> Dict[str, str]:
    """Get environment information."""
    return {
        "python_version": sys.version,
        "path": os.environ.get("PATH", "")
    }

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_array_checksum(array: np.ndarray) -> str:
    """Compute checksum of a numpy array."""
    return hashlib.sha256(array.tobytes()).hexdigest()

def save_fits_image(image: np.ndarray, filepath: Path, metadata: Dict[str, Any]):
    """Save a numpy array as a FITS file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    hdu = fits.PrimaryHDU(image)
    for k, v in metadata.items():
        hdu.header[k] = v
    hdu.writeto(filepath, overwrite=True)

def save_metadata_json(data: List[Dict[str, Any]], filepath: Path):
    """Save metadata list to a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def generate_run_manifest(filepath: Path):
    """Generate a run manifest with git hash, env, and config."""
    manifest = {
        "git_commit": get_git_commit_hash(),
        "env_vars": get_environment_info(),
        "artifact_params": {}, # Would load from config
        "timestamp": "N/A"
    }
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(manifest, f, indent=2)

def write_run_manifest_for_pipeline(filepath: Path):
    """Write the final run manifest for the pipeline."""
    generate_run_manifest(filepath)

def save_run_log(log_data: Dict[str, Any], filepath: Path):
    """Save run log data."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(log_data, f, indent=2)

def write_artifact_manifest(manifest_data: List[Dict[str, Any]], filepath: Path):
    """Write artifact manifest."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(manifest_data, f, indent=2)
