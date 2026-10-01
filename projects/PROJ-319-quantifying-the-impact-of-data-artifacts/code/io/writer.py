"""
File writing utilities: FITS, JSON, manifests.
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from astropy.io import fits

def compute_file_checksum(filepath: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_array_checksum(array: np.ndarray) -> str:
    """
    Compute SHA256 checksum of a numpy array.
    """
    import numpy as np
    return hashlib.sha256(array.tobytes()).hexdigest()

def get_git_commit_hash() -> str:
    """
    Get the current git commit hash.
    """
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def get_environment_info() -> Dict[str, str]:
    """
    Get basic environment information.
    """
    return {
        "python_version": sys.version,
        "path": os.environ.get("PATH", ""),
        "os": os.name
    }

def save_fits_image(filepath: Path, data: np.ndarray, header: Optional[Dict[str, Any]] = None) -> None:
    """
    Save a numpy array as a FITS file.
    """
    hdu = fits.PrimaryHDU(data)
    if header:
        for k, v in header.items():
            hdu.header[k] = v
    hdu.writeto(filepath, overwrite=True)

def save_metadata_json(filepath: Path, metadata: Dict[str, Any]) -> None:
    """
    Save metadata as a JSON file.
    """
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)

def generate_run_manifest(root: Path) -> Dict[str, Any]:
    """
    Generate a run manifest capturing git hash, env, and config.
    """
    from code.config import get_config_summary
    return {
        "git_commit": get_git_commit_hash(),
        "env_vars": get_environment_info(),
        "artifact_params": get_config_summary(),
        "timestamp": subprocess.check_output(['date', '-Iseconds']).decode('ascii').strip()
    }

def write_run_manifest_for_pipeline(root: Path) -> None:
    """
    Write the run manifest to data/processed/run_manifest.json.
    """
    root = Path(root)
    manifest = generate_run_manifest(root)
    output_path = root / "data" / "processed" / "run_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logging.info(f"Run manifest written to {output_path}")

def save_run_log(filepath: Path, log_entries: List[str]) -> None:
    """
    Save run log entries to a file.
    """
    with open(filepath, 'w') as f:
        f.write('\n'.join(log_entries))

def write_artifact_manifest(root: Path, artifacts: Dict[str, str]) -> None:
    """
    Write a manifest of artifacts produced in this run.
    """
    root = Path(root)
    manifest_path = root / "data" / "processed" / "artifact_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(artifacts, f, indent=2)
