"""
Utility functions for data generation, serialization, and checksums.
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

# Import from project API surface
from config import get_config

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_EPSILON_SWEEP = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4]

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return PROJECT_ROOT

def apply_epsilon_floor(value: float, epsilon: float = 1e-6) -> float:
    """Applies an epsilon floor to a value to prevent division by zero."""
    return max(value, epsilon)

def safe_log(value: float, epsilon: float = 1e-10) -> float:
    """Computes log safely, handling zero or negative values."""
    if value <= 0:
        return np.log(epsilon)
    return np.log(value)

def safe_divide(numerator: float, denominator: float, epsilon: float = 1e-10) -> float:
    """Safely divides two numbers, preventing division by zero."""
    if abs(denominator) < epsilon:
        return 0.0
    return numerator / denominator

def check_numerical_stability(matrix: np.ndarray) -> bool:
    """Checks if a matrix contains NaN or Inf values."""
    return not (np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)))

def linear_drift(start: float, end: float, step: int, total_steps: int) -> float:
    """Computes linear drift value for a given step."""
    return start + (end - start) * (step / total_steps)

def exponential_drift(start: float, end: float, step: int, total_steps: int, base: float = 2.0) -> float:
    """Computes exponential drift value for a given step."""
    if total_steps == 0:
        return start
    ratio = step / total_steps
    return start * (base ** (ratio * (np.log(end / start) / np.log(base)) if start != 0 else 0))

def sinusoidal_drift(start: float, end: float, step: int, total_steps: int, frequency: float = 1.0) -> float:
    """Computes sinusoidal drift value for a given step."""
    if total_steps == 0:
        return start
    phase = 2 * np.pi * frequency * (step / total_steps)
    return start + (end - start) * 0.5 * (1 + np.sin(phase))

def get_drift_model(model_name: str = "linear"):
    """Returns the appropriate drift function based on name."""
    models = {
        "linear": linear_drift,
        "exponential": exponential_drift,
        "sinusoidal": sinusoidal_drift
    }
    if model_name not in models:
        raise ValueError(f"Unknown drift model: {model_name}")
    return models[model_name]

def generate_epsilon_sweep_values() -> List[float]:
    """Returns the list of epsilon values for sensitivity analysis."""
    config = get_config()
    if hasattr(config, 'EPSILON_SWEEP_VALUES'):
        return config.EPSILON_SWEEP_VALUES
    return DEFAULT_EPSILON_SWEEP

def compute_checksum(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_to_parquet(df: pd.DataFrame, file_path: Path) -> None:
    """Saves a pandas DataFrame to a Parquet file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False)

def load_from_parquet(file_path: Path) -> pd.DataFrame:
    """Loads a pandas DataFrame from a Parquet file."""
    return pd.read_parquet(file_path)

def setup_generation_logger(name: str = "data_generation") -> logging.Logger:
    """Sets up and returns a logger for data generation tasks."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    return logger

def log_generation_progress(logger: logging.Logger, current: int, total: int, success: int, failure: int) -> None:
    """Logs the current progress of data generation."""
    logger.info(f"Progress: {current}/{total} | Success: {success} | Failures: {failure}")

def log_solver_success(logger: logging.Logger, scaling_factor: float) -> None:
    """Logs a successful solver execution."""
    logger.debug(f"Solver succeeded with scaling factor: {scaling_factor}")

def log_solver_failure(logger: logging.Logger, error_msg: str) -> None:
    """Logs a failed solver execution."""
    logger.warning(f"Solver failed: {error_msg}")

def log_numerical_warning(logger: logging.Logger, message: str) -> None:
    """Logs a numerical stability warning."""
    logger.warning(f"Numerical Warning: {message}")

def log_skipped_instance(logger: logging.Logger, index: int, reason: str) -> None:
    """Logs a skipped instance due to failure."""
    logger.debug(f"Skipped instance {index}: {reason}")

def generate_checksum_for_dataset(data_file: Path, checksum_file: Path) -> None:
    """Generates and saves the SHA-256 checksum for a dataset file."""
    checksum = compute_checksum(data_file)
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {data_file.name}\n")
    logging.info(f"Checksum saved to {checksum_file}")

def compute_and_store_checksums(file_paths: List[Path]) -> Dict[str, str]:
    """Computes and stores checksums for a list of files."""
    checksums = {}
    for path in file_paths:
        if path.exists():
            checksums[str(path)] = compute_checksum(path)
        else:
            logging.warning(f"File not found for checksum: {path}")
    return checksums

def main():
    """Main function for testing utilities."""
    print("Utils module loaded successfully.")

if __name__ == "__main__":
    main()
