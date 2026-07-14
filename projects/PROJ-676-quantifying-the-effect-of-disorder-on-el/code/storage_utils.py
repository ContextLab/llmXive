"""
Storage utilities for the disorder transport project.

Handles HDF5 storage with SHA-256 checksum generation and logging to
data/metadata/provenance.json.
"""
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import h5py
import numpy as np

from code.config import get_config


def _get_provenance_path() -> Path:
    """Return the path to the provenance JSON file."""
    config = get_config()
    return Path(config.DATA_METADATA_DIR) / "provenance.json"


def _load_provenance() -> Dict[str, Any]:
    """Load the existing provenance file or return a fresh schema."""
    path = _get_provenance_path()
    if not path.exists():
        return {
            "schema_version": "1.0.0",
            "description": "Provenance log for all generated data artifacts in the disorder transport project.",
            "entries": []
        }

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_provenance(data: Dict[str, Any]) -> None:
    """Save the provenance data to disk."""
    path = _get_provenance_path()
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _compute_sha256(data: Union[np.ndarray, bytes]) -> str:
    """Compute SHA-256 hash of the provided data."""
    if isinstance(data, np.ndarray):
        # Serialize numpy array to bytes
        raw_bytes = data.tobytes()
    elif isinstance(data, bytes):
        raw_bytes = data
    else:
        raise TypeError(f"Unsupported data type for hashing: {type(data)}")

    return hashlib.sha256(raw_bytes).hexdigest()


def log_provenance_entry(
    artifact_path: str,
    artifact_type: str,
    checksum: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a new entry to the provenance file.

    Args:
        artifact_path: Relative path to the artifact from project root.
        artifact_type: Type of artifact (e.g., 'hamiltonian', 'eigenstate').
        checksum: SHA-256 checksum of the artifact data.
        metadata: Optional additional metadata (e.g., W, L, seed).
    """
    config = get_config()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "artifact_path": artifact_path,
        "artifact_type": artifact_type,
        "checksum": checksum,
        "metadata": metadata or {},
        "config_snapshot": {
            "random_seed": config.RANDOM_SEED,
            "num_realizations": config.NUM_REALIZATIONS,
        }
    }

    provenance = _load_provenance()
    provenance["entries"].append(entry)
    _save_provenance(provenance)


def save_hamiltonian_to_hdf5(
    hamiltonian: np.ndarray,
    disorder_params: Dict[str, Any],
    realization_index: int,
    output_dir: Optional[str] = None
) -> str:
    """
    Save a Hamiltonian matrix to HDF5 and log to provenance.

    Args:
        hamiltonian: The L x L Hamiltonian matrix.
        disorder_params: Dictionary with keys 'W' (disorder strength) and 'L' (system size).
        realization_index: Index of this disorder realization.
        output_dir: Optional override for output directory. Defaults to config.DATA_RAW_DIR.

    Returns:
        Relative path to the saved HDF5 file.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.DATA_RAW_DIR

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"ham_L{disorder_params['L']}_W{disorder_params['W']}_idx{realization_index}.h5"
    file_path = output_path / filename
    relative_path = str(Path("data/raw") / filename)

    # Compute checksum of the raw numpy data
    checksum = _compute_sha256(hamiltonian)

    with h5py.File(file_path, "w") as hf:
        hf.create_dataset("H", data=hamiltonian, compression="gzip", compression_opts=4)
        hf.attrs["W"] = disorder_params["W"]
        hf.attrs["L"] = disorder_params["L"]
        hf.attrs["realization_index"] = realization_index
        hf.attrs["timestamp"] = datetime.utcnow().isoformat() + "Z"
        hf.attrs["checksum"] = checksum

    log_provenance_entry(
        artifact_path=relative_path,
        artifact_type="hamiltonian",
        checksum=checksum,
        metadata=disorder_params
    )

    return relative_path


def load_hamiltonian_from_hdf5(file_path: str) -> np.ndarray:
    """
    Load a Hamiltonian from an HDF5 file.

    Args:
        file_path: Path to the HDF5 file.

    Returns:
        The Hamiltonian matrix as a numpy array.
    """
    with h5py.File(file_path, "r") as hf:
        return np.array(hf["H"])


def save_eigenstates_to_hdf5(
    eigenvalues: np.ndarray,
    eigenstates: np.ndarray,
    disorder_params: Dict[str, Any],
    realization_index: int,
    output_dir: Optional[str] = None
) -> str:
    """
    Save eigenvalues and eigenstates to HDF5 and log to provenance.

    Args:
        eigenvalues: 1D array of eigenvalues.
        eigenstates: 2D array where columns are eigenstates.
        disorder_params: Dictionary with keys 'W', 'L'.
        realization_index: Index of this disorder realization.
        output_dir: Optional override for output directory. Defaults to config.DATA_PROCESSED_DIR.

    Returns:
        Relative path to the saved HDF5 file.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.DATA_PROCESSED_DIR

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"eigen_L{disorder_params['L']}_W{disorder_params['W']}_idx{realization_index}.h5"
    file_path = output_path / filename
    relative_path = str(Path("data/processed") / filename)

    # Compute checksums
    ev_checksum = _compute_sha256(eigenvalues)
    es_checksum = _compute_sha256(eigenstates)
    combined_checksum = hashlib.sha256((ev_checksum + es_checksum).encode()).hexdigest()

    with h5py.File(file_path, "w") as hf:
        hf.create_dataset("eigenvalues", data=eigenvalues, compression="gzip", compression_opts=4)
        hf.create_dataset("eigenstates", data=eigenstates, compression="gzip", compression_opts=4)
        hf.attrs["W"] = disorder_params["W"]
        hf.attrs["L"] = disorder_params["L"]
        hf.attrs["realization_index"] = realization_index
        hf.attrs["timestamp"] = datetime.utcnow().isoformat() + "Z"
        hf.attrs["checksum"] = combined_checksum

    log_provenance_entry(
        artifact_path=relative_path,
        artifact_type="eigenstates",
        checksum=combined_checksum,
        metadata=disorder_params
    )

    return relative_path


def save_localization_length(
    localization_length: float,
    uncertainty: float,
    fit_params: Dict[str, Any],
    disorder_params: Dict[str, Any],
    realization_indices: List[int],
    output_dir: Optional[str] = None
) -> str:
    """
    Save localization length results to JSON and log to provenance.

    Args:
        localization_length: The computed localization length xi.
        uncertainty: Uncertainty in xi.
        fit_params: Parameters from the finite-size scaling fit.
        disorder_params: Dictionary with 'W' and 'L' (representative L).
        realization_indices: List of realization indices included in this average.
        output_dir: Optional override. Defaults to config.DATA_PROCESSED_DIR.

    Returns:
        Relative path to the saved JSON file.
    """
    config = get_config()
    if output_dir is None:
        output_dir = config.DATA_PROCESSED_DIR

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = f"xi_W{disorder_params['W']}.json"
    file_path = output_path / filename
    relative_path = str(Path("data/processed") / filename)

    data = {
        "xi": localization_length,
        "uncertainty": uncertainty,
        "fit_params": fit_params,
        "W": disorder_params["W"],
        "L_range": [min(disorder_params.get("L_range", [])), max(disorder_params.get("L_range", []))],
        "num_realizations": len(realization_indices),
        "realization_indices": realization_indices,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checksum": hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    }

    # Compute checksum of the content
    checksum = data.pop("checksum")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    log_provenance_entry(
        artifact_path=relative_path,
        artifact_type="localization_length",
        checksum=checksum,
        metadata={"W": disorder_params["W"]}
    )

    return relative_path
