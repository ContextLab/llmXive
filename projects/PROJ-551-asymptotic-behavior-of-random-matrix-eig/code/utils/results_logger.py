"""
Results logging utility for recording simulation outputs to data/processed/.

This module handles the serialization of eigenvalue results, perturbation parameters,
and metadata into structured JSON files with checksums for reproducibility.
"""
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_project_paths, ensure_directories
from utils.checksum import compute_file_checksum


def _compute_record_hash(record: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 hash of a result record for integrity verification.
    """
    # Sort keys to ensure deterministic serialization
    json_str = json.dumps(record, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def record_simulation_result(
    eigenvalues: List[float],
    perturbation_config: Dict[str, Any],
    simulation_params: Dict[str, Any],
    outlier_info: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Record a single simulation run's results to a JSON file in data/processed/.

    Args:
        eigenvalues: List of computed top eigenvalues (floats).
        perturbation_config: Dictionary describing the perturbation (type, norm, sparsity, etc.).
        simulation_params: Dictionary of simulation settings (N, seed, tolerance, etc.).
        outlier_info: Optional dictionary containing outlier detection results.
        output_dir: Optional override for the output directory (default: data/processed/).

    Returns:
        Path to the created JSON file.

    Raises:
        ValueError: If required fields are missing.
        IOError: If the file cannot be written.
    """
    if not eigenvalues:
        raise ValueError("eigenvalues list cannot be empty")
    if not perturbation_config:
        raise ValueError("perturbation_config cannot be empty")
    if not simulation_params:
        raise ValueError("simulation_params cannot be empty")

    paths = get_project_paths()
    if output_dir:
        target_dir = Path(output_dir)
    else:
        target_dir = paths.processed

    ensure_directories(target_dir)

    timestamp = datetime.utcnow().isoformat() + "Z"
    record_id = f"run_{simulation_params.get('seed', 'unknown')}_{timestamp.replace(':', '-').replace('.', '_')}"

    record = {
        "id": record_id,
        "timestamp": timestamp,
        "simulation_params": simulation_params,
        "perturbation_config": perturbation_config,
        "eigenvalues": eigenvalues,
        "outlier_info": outlier_info,
        "record_hash": _compute_record_hash({
            "eigenvalues": eigenvalues,
            "perturbation_config": perturbation_config,
            "simulation_params": simulation_params
        })
    }

    # Create filename based on seed and timestamp
    safe_seed = str(simulation_params.get('seed', 'unknown'))
    safe_time = timestamp.replace(":", "-").replace(".", "_").replace("T", "_")
    filename = f"result_{safe_seed}_{safe_time}.json"
    file_path = target_dir / filename

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2)
        
        # Append checksum to a manifest if one exists, or create new
        checksum = compute_file_checksum(file_path)
        manifest_path = target_dir / "manifest.json"
        
        manifest_data = {"files": []}
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as mf:
                manifest_data = json.load(mf)
        
        manifest_data["files"].append({
            "filename": filename,
            "checksum": checksum,
            "created_at": timestamp
        })
        
        with open(manifest_path, 'w', encoding='utf-8') as mf:
            json.dump(manifest_data, mf, indent=2)

        return str(file_path)
    except IOError as e:
        raise IOError(f"Failed to write results to {file_path}: {e}") from e


def append_to_aggregated_results(
    results_list: List[Dict[str, Any]],
    output_file: str = "aggregated_results.json"
) -> str:
    """
    Append a list of result records to an aggregated JSON file.

    Args:
        results_list: List of result records (dicts).
        output_file: Name of the file to append to (relative to data/processed/).

    Returns:
        Path to the aggregated file.
    """
    paths = get_project_paths()
    target_dir = paths.processed
    file_path = target_dir / output_file

    existing_data = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    existing_data.extend(results_list)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)

    return str(file_path)