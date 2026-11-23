"""
Trajectory I/O with integrity verification.

Handles saving and loading of trajectory data to/from data/raw/
with SHA-256 checksums for data integrity.
"""
import hashlib
import json
import os
import gzip
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import asdict

import numpy as np

from .generator import TrajectoryData


class ChecksumMismatchError(Exception):
    """Raised when a loaded file's checksum does not match the stored one."""
    pass


class TrajectoryFileNotFoundError(Exception):
    """Raised when the requested trajectory file does not exist."""
    pass


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def _serialize_trajectory(trajectory: TrajectoryData) -> Dict[str, Any]:
    """Convert TrajectoryData to a JSON-serializable dictionary."""
    data_dict = asdict(trajectory)
    # Convert numpy arrays to lists for JSON serialization
    for key, value in data_dict.items():
        if isinstance(value, np.ndarray):
            data_dict[key] = value.tolist()
        elif isinstance(value, (np.integer, np.floating)):
            data_dict[key] = value.item()
    return data_dict


def _deserialize_trajectory(data: Dict[str, Any]) -> TrajectoryData:
    """Convert a dictionary back to a TrajectoryData object."""
    # Convert lists back to numpy arrays where expected
    if 'time' in data and isinstance(data['time'], list):
        data['time'] = np.array(data['time'])
    if 'state' in data and isinstance(data['state'], list):
        data['state'] = np.array(data['state'])
    if 'metadata' in data and isinstance(data['metadata'], dict):
        # Ensure metadata values are correct types if needed
        pass
    return TrajectoryData(**data)


def save_trajectory(
    trajectory: TrajectoryData,
    output_dir: str,
    filename: str,
    compress: bool = True
) -> Tuple[Path, str]:
    """
    Save a trajectory to disk with a SHA-256 checksum.

    Args:
        trajectory: The trajectory data to save.
        output_dir: Directory to save the file (e.g., 'data/raw').
        filename: Base filename (without extension).
        compress: If True, save as .json.gz; otherwise .json.

    Returns:
        Tuple of (full_path, sha256_checksum).
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ext = ".json.gz" if compress else ".json"
    file_path = output_path / f"{filename}{ext}"
    checksum_path = output_path / f"{filename}.sha256"

    # Serialize
    data_dict = _serialize_trajectory(trajectory)
    # Add a hash of the content itself for double verification if needed
    # but primarily we hash the file bytes.

    if compress:
        import gzip
        json_str = json.dumps(data_dict, indent=2)
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2)

    # Compute and save checksum
    checksum = _compute_sha256(file_path)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(checksum)

    return file_path, checksum


def load_trajectory(
    file_path: str,
    verify_checksum: bool = True
) -> TrajectoryData:
    """
    Load a trajectory from disk and optionally verify its checksum.

    Args:
        file_path: Path to the .json or .json.gz file.
        verify_checksum: If True, check against the .sha256 file.

    Returns:
        TrajectoryData object.

    Raises:
        TrajectoryFileNotFoundError: If the file does not exist.
        ChecksumMismatchError: If the checksum verification fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise TrajectoryFileNotFoundError(f"Trajectory file not found: {file_path}")

    # Load data
    if path.suffix == ".gz":
        import gzip
        with gzip.open(path, 'rt', encoding='utf-8') as f:
            data_dict = json.load(f)
    else:
        with open(path, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)

    trajectory = _deserialize_trajectory(data_dict)

    if verify_checksum:
        checksum_file = path.with_suffix(path.suffix + ".sha256" if path.suffix == ".json" else ".sha256")
        # Handle .json.gz -> .sha256 logic correctly
        if path.suffix == ".gz":
            checksum_file = path.with_suffix(".sha256")
        elif path.suffix == ".json":
            checksum_file = path.with_suffix(".sha256")
        
        if checksum_file.exists():
            with open(checksum_file, 'r', encoding='utf-8') as f:
                stored_checksum = f.read().strip()
            
            computed_checksum = _compute_sha256(path)
            
            if stored_checksum != computed_checksum:
                raise ChecksumMismatchError(
                    f"Checksum mismatch for {file_path}. "
                    f"Stored: {stored_checksum}, Computed: {computed_checksum}"
                )
        else:
            # Warn but do not fail if checksum file is missing, 
            # unless strict mode is enforced (not implemented here).
            pass

    return trajectory


def generate_filename(
    N: int,
    sigma: float,
    seed: int,
    trial: int = 0,
    suffix: Optional[str] = None
) -> str:
    """
    Generate a standardized filename for a trajectory.
    
    Format: traj_N{N}_sigma{sigma:.4f}_seed{seed}_trial{trial}[_suffix]
    """
    base = f"traj_N{N}_sigma{sigma:.4f}_seed{seed}_trial{trial}"
    if suffix:
        base += f"_{suffix}"
    return base
