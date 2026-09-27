"""
I/O Writer module for saving images, metadata, and run manifests.
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from astropy.io import fits
    HAS_ASTROPY = True
except ImportError:
    HAS_ASTROPY = False

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_array_checksum(arr) -> str:
    """Compute SHA-256 checksum of a numpy array."""
    import numpy as np
    return hashlib.sha256(arr.tobytes()).hexdigest()

def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def get_environment_info() -> Dict[str, str]:
    """Get basic environment information."""
    return {
        "python_version": sys.version,
        "path": os.environ.get("PATH", ""),
        "os": os.name
    }

def save_fits_image(data: Any, file_path: Path, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Save a numpy array as a FITS file."""
    if not HAS_ASTROPY:
        raise ImportError("Astropy is required to save FITS files.")
    import numpy as np
    hdu = fits.PrimaryHDU(np.array(data))
    if metadata:
        for k, v in metadata.items():
            if len(str(v)) <= 64: # FITS header value limit
                hdu.header[k] = str(v)
    hdu.writeto(file_path, overwrite=True)

def save_metadata_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save a dictionary as a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def generate_run_manifest(root: Path) -> Dict[str, Any]:
    """Generate a run manifest dictionary."""
    return {
        "git_commit": get_git_commit_hash(),
        "env_vars": get_environment_info(),
        "timestamp": datetime.now().isoformat(),
        "artifact_params": {
            "noise_levels": [0.01, 0.05, 0.10],
            "saturation_range": {"start": 0.0, "end": 0.5, "step": 0.05}
        }
    }

def write_run_manifest_for_pipeline(root: Path) -> None:
    """Write the run manifest to data/processed/run_manifest.json."""
    manifest = generate_run_manifest(root)
    output_path = root / "data" / "processed" / "run_manifest.json"
    save_metadata_json(manifest, output_path)
    logging.getLogger("llmXive").info(f"Run manifest written to {output_path}")

def save_run_log(log_path: Path, content: str) -> None:
    """Append content to a log file."""
    with open(log_path, 'a') as f:
        f.write(content + "\n")

def write_artifact_manifest(manifest: Dict[str, Any], file_path: Path) -> None:
    """Write an artifact manifest JSON."""
    save_metadata_json(manifest, file_path)
