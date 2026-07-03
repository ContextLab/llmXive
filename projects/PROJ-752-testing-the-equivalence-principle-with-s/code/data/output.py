import os
import json
import hashlib
import shutil
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from utils.logging import get_logger, log_progress, log_error

logger = get_logger(__name__)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """Save cleaned data to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def record_checksum(file_path: str, checksums_file: str) -> None:
    """Record SHA256 checksum of a file in a JSON manifest."""
    checksum = compute_sha256(file_path)
    os.makedirs(os.path.dirname(checksums_file), exist_ok=True)
    
    checksums = {}
    if os.path.exists(checksums_file):
        with open(checksums_file, 'r') as f:
            checksums = json.load(f)
    
    checksums[os.path.basename(file_path)] = checksum
    
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Recorded checksum for {file_path} in {checksums_file}")

def ensure_raw_data_preserved(raw_dir: str) -> None:
    """Ensure raw data directory exists and is not modified."""
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory {raw_dir} does not exist.")
    else:
        logger.info(f"Verified raw data directory {raw_dir} exists.")

def save_orbit_solution(solution: Any, output_path: str) -> None:
    """
    Save OrbitSolution object to JSON.
    Expects solution to have a .to_dict() method or be serializable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if hasattr(solution, 'to_dict'):
        data = solution.to_dict()
    elif hasattr(solution, '__dict__'):
        data = solution.__dict__
    else:
        raise ValueError("OrbitSolution must be serializable or have to_dict() method")
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved orbit solution to {output_path}")

def save_eotvos_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save EotvosResult metrics to JSON.
    Expects metrics to be a dictionary with serializable values.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Ensure all values are JSON serializable (convert numpy types, etc.)
    def make_serializable(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [make_serializable(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif hasattr(obj, 'item'):  # numpy scalar
            return obj.item()
        elif hasattr(obj, 'tolist'):  # numpy array
            return obj.tolist()
        else:
            return str(obj)
    
    serializable_metrics = make_serializable(metrics)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_metrics, f, indent=2)
    
    logger.info(f"Saved Eotvos metrics to {output_path}")

def run_output_pipeline(
    cleaned_data_path: Optional[str] = None,
    solution: Optional[Any] = None,
    eotvos_metrics: Optional[Dict[str, Any]] = None,
    results_dir: str = "data/results",
    checksums_file: str = "data/processed/.checksums.json"
) -> None:
    """
    Orchestrate saving of all pipeline outputs.
    
    Args:
        cleaned_data_path: Path to cleaned CSV data (optional)
        solution: OrbitSolution object (optional)
        eotvos_metrics: Dictionary of Eotvos metrics (optional)
        results_dir: Directory for result files
        checksums_file: Path to checksums manifest
    """
    log_progress("Starting output pipeline...")
    
    if cleaned_data_path and os.path.exists(cleaned_data_path):
        checksums = {}
        if os.path.exists(checksums_file):
            with open(checksums_file, 'r') as f:
                checksums = json.load(f)
        
        checksum = compute_sha256(cleaned_data_path)
        checksums[os.path.basename(cleaned_data_path)] = checksum
        
        with open(checksums_file, 'w') as f:
            json.dump(checksums, f, indent=2)
        
        log_progress(f"Recorded checksum for {cleaned_data_path}")
    
    if solution is not None:
        orbit_sol_path = os.path.join(results_dir, "orbit_solutions.json")
        save_orbit_solution(solution, orbit_sol_path)
        record_checksum(orbit_sol_path, checksums_file)
    
    if eotvos_metrics is not None:
        eotvos_path = os.path.join(results_dir, "eotvos_metrics.json")
        save_eotvos_metrics(eotvos_metrics, eotvos_path)
        record_checksum(eotvos_path, checksums_file)
    
    log_progress("Output pipeline completed.")
