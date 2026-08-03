"""
Utility functions for data generation, including numerical stability,
drift models, and checksumming operations.
"""
import numpy as np
from typing import Union, Optional, Callable, List
import json
import hashlib
from pathlib import Path
import logging
import os
import yaml

logger = logging.getLogger(__name__)

def apply_epsilon_floor(value: float, epsilon: float) -> float:
    """
    Ensures a value is at least epsilon to prevent numerical instability.
    """
    return max(value, epsilon)

def safe_log(value: float, epsilon: float = 1e-10) -> float:
    """
    Computes log safely by clamping the input to a minimum epsilon.
    """
    return np.log(apply_epsilon_floor(value, epsilon))

def safe_divide(numerator: float, denominator: float, epsilon: float = 1e-10) -> float:
    """
    Performs division safely by ensuring the denominator is not zero.
    """
    safe_denominator = apply_epsilon_floor(abs(denominator), epsilon)
    if denominator < 0:
        safe_denominator = -safe_denominator
    return numerator / safe_denominator

def check_numerical_stability(value: float, name: str = "value") -> bool:
    """
    Checks if a value is finite (not NaN or Inf).
    """
    is_finite = np.isfinite(value)
    if not is_finite:
        logger.warning(f"Numerical instability detected in {name}: {value}")
    return is_finite

def linear_drift(x: float, slope: float = 0.01) -> float:
    """Linear drift model."""
    return slope * x

def exponential_drift(x: float, rate: float = 0.001) -> float:
    """Exponential drift model."""
    return np.exp(rate * x) - 1

def sinusoidal_drift(x: float, amplitude: float = 1.0, frequency: float = 0.1) -> float:
    """Sinusoidal drift model."""
    return amplitude * np.sin(frequency * x)

def get_drift_model(model_type: str) -> Callable[[float], float]:
    """Factory function to retrieve a drift model."""
    models = {
        'linear': linear_drift,
        'exponential': exponential_drift,
        'sinusoidal': sinusoidal_drift
    }
    if model_type not in models:
        raise ValueError(f"Unknown drift model type: {model_type}")
    return models[model_type]

def generate_epsilon_sweep_values(base: float = 1e-6, count: int = 10) -> List[float]:
    """Generates a list of epsilon values for sensitivity analysis."""
    return [base * (10 ** i) for i in range(count)]

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_json_with_checksum(data: dict, output_path: Union[str, Path]) -> None:
    """
    Saves data to a JSON file and appends a checksum field.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # First pass: compute checksum of the content without the checksum field
    # To ensure determinism, we serialize without the checksum first
    temp_data = data.copy()
    if 'checksum' in temp_data:
        del temp_data['checksum']
    
    content_str = json.dumps(temp_data, sort_keys=True, indent=2)
    checksum = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
    
    temp_data['checksum'] = checksum
    
    with open(path, 'w') as f:
        json.dump(temp_data, f, indent=2)
    logger.info(f"Saved {path} with checksum {checksum}")

def compute_and_store_checksums() -> bool:
    """
    Computes SHA-256 checksums for all files in data/ and updates
    the project's central state file.
    
    This function implements the core logic for T001d.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    state_dir = project_root / "state" / "projects"
    state_file = state_dir / "PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return False
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    file_count = 0
    
    logger.info(f"Scanning {data_dir} for files...")
    
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(project_root)
            try:
                checksum = compute_checksum(file_path)
                checksums[str(rel_path)] = checksum
                file_count += 1
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")
                return False
    
    logger.info(f"Computed checksums for {file_count} files.")
    
    # Load existing state or create new
    state_data = {}
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}. Creating new one.")
            state_data = {}
    
    # Update artifact_hashes
    state_data['artifact_hashes'] = checksums
    state_data['last_updated'] = str(Path(__file__).resolve().parent) # Placeholder timestamp logic
    
    # Write back
    try:
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=True)
        logger.info(f"Successfully updated state file: {state_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        return False
