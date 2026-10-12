"""
File writing utilities: FITS, JSON, manifests, and checksum‑aware saving.
"""
import hashlib
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
from astropy.io import fits

logger = logging.getLogger(__name__)


def compute_file_checksum(filepath: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_array_checksum(array: np.ndarray) -> str:
    """
    Compute SHA256 checksum of a numpy array.
    """
    return hashlib.sha256(array.tobytes()).hexdigest()


def get_git_commit_hash() -> str:
    """
    Get the current git commit hash.
    """
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except Exception:
        return "unknown"


def get_environment_info() -> Dict[str, str]:
    """
    Get basic environment information.
    """
    return {
        "python_version": sys.version,
        "path": os.environ.get("PATH", ""),
        "os": os.name,
    }


def save_fits_image(
    filepath: Path,
    data: np.ndarray,
    header: Optional[Dict[str, Any]] = None,
) -> None:
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
    with open(filepath, "w") as f:
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
        "timestamp": subprocess.check_output(
            ["date", "-Iseconds"]
        )
        .decode("ascii")
        .strip(),
    }


def write_run_manifest_for_pipeline(root: Path) -> None:
    """
    Write the run manifest to data/processed/run_manifest.json.
    """
    root = Path(root)
    manifest = generate_run_manifest(root)
    output_path = root / "data" / "processed" / "run_manifest.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Run manifest written to {output_path}")


def save_run_log(filepath: Path, log_entries: List[str]) -> None:
    """
    Save run log entries to a file.
    """
    with open(filepath, "w") as f:
        f.write("\n".join(log_entries))


def write_artifact_manifest(root: Path, artifacts: Dict[str, str]) -> None:
    """
    Write a manifest of artifacts produced in this run.
    """
    root = Path(root)
    manifest_path = root / "data" / "processed" / "artifact_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(artifacts, f, indent=2)


def save_with_checksum(
    filepath: Path,
    data: Optional[np.ndarray] = None,
    header: Optional[Dict[str, Any]] = None,
    text: Optional[str] = None,
) -> None:
    """
    Save either a FITS image (when ``data`` is provided) or a plain text
    file (when ``text`` is provided) and write a sibling ``.sha256``
    checksum file.

    The checksum file is written to ``<filepath>.sha256`` and contains
    the hexadecimal SHA‑256 digest of the written artifact.

    Parameters
    ----------
    filepath : Path
        Destination path for the primary artifact.
    data : np.ndarray, optional
        Image data to be saved as a FITS file. If supplied, ``text`` must be
        ``None``.
    header : dict, optional
        Header dictionary to be added to the FITS file.
    text : str, optional
        Text content to be written verbatim. If supplied, ``data`` must be
        ``None``.

    Raises
    ------
    ValueError
        If both ``data`` and ``text`` are ``None`` or both are supplied.
    """
    if (data is None and text is None) or (data is not None and text is not None):
        raise ValueError(
            "Provide exactly one of 'data' (for FITS) or 'text' (for plain file)."
        )

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if data is not None:
        # Save as FITS
        save_fits_image(filepath, data, header)
    else:
        # Save plain text
        with open(filepath, "w") as f:
            f.write(text)

    # Compute checksum of the written artifact
    checksum = compute_file_checksum(filepath)

    # Write checksum file alongside the artifact
    checksum_path = filepath.with_suffix(filepath.suffix + ".sha256")
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {filepath.name}")

    logger.info(
        f"Saved artifact '{filepath}' and checksum file '{checksum_path}'."
    )

# Exported symbols for ``from code.io.writer import *``
__all__ = [
    "compute_file_checksum",
    "compute_array_checksum",
    "get_git_commit_hash",
    "get_environment_info",
    "save_fits_image",
    "save_metadata_json",
    "generate_run_manifest",
    "write_run_manifest_for_pipeline",
    "save_run_log",
    "write_artifact_manifest",
    "save_with_checksum",
]
