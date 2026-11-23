"""
Data output utilities for T019.

Provides functions to compute checksums, save cleaned data,
and record artifact hashes in the project state file.
"""
import os
import json
import hashlib
import shutil
import pandas as pd
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
      Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save cleaned DataFrame to CSV.
    
    Args:
        df: The cleaned DataFrame.
        output_path: Destination path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def ensure_raw_data_preserved(raw_dir: Path) -> None:
    """
    Verify that the raw data directory exists and is non-empty.
    Raises an error if raw data is missing or empty, ensuring preservation.
    
    Args:
        raw_dir: Path to the raw data directory.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    if not any(raw_dir.iterdir()):
        raise ValueError(f"Raw data directory is empty: {raw_dir}")
        
    logger.info(f"Verified raw data preservation in {raw_dir}")

def record_checksum(state_file: Path, artifact_name: str, checksum: str, path: str) -> None:
    """
    Record the checksum of an artifact in the project state YAML file.
    Implements Constitution Principle III.
    
    Args:
        state_file: Path to the state YAML file.
        artifact_name: Name of the artifact (e.g., 'cleaned_slr_data.csv').
        checksum: SHA-256 checksum string.
        path: Relative or absolute path to the artifact.
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {}
        
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
        
    state["artifact_hashes"][artifact_name] = {
        "checksum": checksum,
        "path": str(path),
        "algorithm": "sha256"
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
        
    logger.info(f"Recorded checksum for {artifact_name} in {state_file}")

def save_orbit_solution(solution: Any, output_path: Path) -> None:
    """
    Save OrbitSolution object to JSON.
    
    Args:
        solution: The OrbitSolution object.
        output_path: Destination path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Convert to dict if possible, or use default
    try:
        data = solution.to_dict() if hasattr(solution, 'to_dict') else str(solution)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save orbit solution: {e}")
        # Fallback
        with open(output_path, 'w') as f:
            f.write(str(solution))

def save_eotvos_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Save Eötvös metrics to JSON.
    
    Args:
        metrics: Dictionary of metrics.
        output_path: Destination path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def run_output_pipeline(cleaned_df: pd.DataFrame, state_file: Path) -> str:
    """
    Run the full T019 output pipeline: save CSV, compute checksum, record state.
    
    Args:
        cleaned_df: The cleaned DataFrame.
        state_file: Path to the state file.
        
    Returns:
        The computed checksum.
    """
    output_path = Path("data/processed/cleaned_slr_data.csv")
    save_cleaned_data(cleaned_df, output_path)
    
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("Output file missing or empty after save.")
        
    checksum = compute_sha256(output_path)
    record_checksum(state_file, "cleaned_slr_data.csv", checksum, str(output_path))
    
    return checksum
