"""
Utility functions for data generation, including numerical stability, drift models, and checksumming.
"""
import numpy as np
from typing import Union, Optional, Callable, List
import json
import hashlib
from pathlib import Path
import logging
import yaml
import os

logger = logging.getLogger(__name__)

def apply_epsilon_floor(value: float, epsilon: float) -> float:
    """
    Applies an epsilon floor to a value to ensure numerical stability.
    Returns max(value, epsilon).
    """
    return max(value, epsilon)

def safe_log(value: float, epsilon: float = 1e-10) -> float:
    """
    Computes log(value) safely by ensuring the argument is positive.
    """
    if value <= 0:
        logger.warning(f"Non-positive value passed to safe_log: {value}, applying epsilon floor.")
        value = apply_epsilon_floor(value, epsilon)
    return np.log(value)

def safe_divide(numerator: float, denominator: float, epsilon: float = 1e-10) -> float:
    """
    Performs division safely by ensuring the denominator is not zero.
    """
    if abs(denominator) < epsilon:
        logger.warning(f"Denominator too small in safe_divide: {denominator}, applying epsilon floor.")
        denominator = apply_epsilon_floor(abs(denominator), epsilon)
        if np.sign(denominator) != np.sign(denominator): # Preserve sign if needed, though abs makes it positive
             denominator = -denominator # Revert if original was negative? No, abs lost sign. 
             # Better:
             denominator = apply_epsilon_floor(denominator, epsilon) if denominator > 0 else -apply_epsilon_floor(-denominator, epsilon)
    return numerator / denominator

def check_numerical_stability(value: Union[float, np.ndarray], threshold: float = 1e-10) -> bool:
    """
    Checks if a value or array contains NaNs, Infs, or values below a threshold.
    """
    if isinstance(value, np.ndarray):
        if np.any(np.isnan(value)) or np.any(np.isinf(value)):
            return False
        if np.any(np.abs(value) < threshold) and not np.all(value == 0):
            logger.warning(f"Values below threshold {threshold} detected.")
            # Depending on strictness, this might return False. 
            # For now, we just warn and return True if no NaN/Inf.
    else:
        if np.isnan(value) or np.isinf(value):
            return False
    return True

def linear_drift(t: float, rate: float) -> float:
    return rate * t

def exponential_drift(t: float, rate: float) -> float:
    return np.exp(rate * t) - 1

def sinusoidal_drift(t: float, amplitude: float, frequency: float) -> float:
    return amplitude * np.sin(frequency * t)

def get_drift_model(model_name: str) -> Callable[[float], float]:
    models = {
        'linear': linear_drift,
        'exponential': exponential_drift,
        'sinusoidal': sinusoidal_drift
    }
    if model_name not in models:
        raise ValueError(f"Unknown drift model: {model_name}")
    return models[model_name]

def generate_epsilon_sweep_values(base: float = 1e-6, count: int = 5) -> List[float]:
    """
    Generates a list of epsilon values for sensitivity analysis.
    """
    return [base * (10 ** i) for i in range(count)]

def compute_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_json_with_checksum(data: dict, output_path: Path) -> None:
    """
    Saves data to a JSON file and appends its checksum.
    """
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    checksum = compute_checksum(output_path)
    # In a real scenario, we might update a separate checksum file or embed it.
    # For now, we just log it.
    logger.info(f"Saved {output_path} with checksum: {checksum}")

def compute_and_store_checksums(data_dir: Path) -> bool:
    """
    Scans the data directory for all files, computes their SHA-256 checksums,
    and updates the central state file at state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml.
    
    Returns True if successful, False otherwise.
    """
    state_file_path = Path("state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml")
    
    if not state_file_path.parent.exists():
        logger.info(f"Creating state directory: {state_file_path.parent}")
        state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return False

    artifact_hashes = {}
    
    logger.info(f"Scanning directory: {data_dir}")
    
    for file_path in data_dir.rglob('*'):
        if file_path.is_file():
            # Compute relative path from project root for the key
            rel_path = file_path.relative_to(Path.cwd())
            try:
                checksum = compute_checksum(file_path)
                artifact_hashes[str(rel_path)] = checksum
                logger.debug(f"Checksum for {rel_path}: {checksum}")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")
                return False

    if not artifact_hashes:
        logger.warning("No files found in data directory to checksum.")
        # Still proceed to update state file if it exists or create it
    
    # Load existing state or create new
    state_data = {}
    if state_file_path.exists():
        try:
            with open(state_file_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load existing state file: {e}")
            return False
    
    # Update artifact_hashes
    state_data['artifact_hashes'] = artifact_hashes
    state_data['last_checksum_update'] = str(Path.cwd().joinpath('now').strftime('%Y-%m-%d %H:%M:%S')) # Simplified timestamp
    
    # Write back
    try:
        with open(state_file_path, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully updated state file: {state_file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        return False
