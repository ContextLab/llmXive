import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from config import get_config

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def setup_generation_logger(name: str = "generation") -> logging.Logger:
    """Setup a logger for data generation tasks."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def log_generation_progress(logger: logging.Logger, current: int, total: int, msg: str = ""):
    """Log progress of generation tasks."""
    pct = (current / total) * 100 if total > 0 else 0
    logger.info(f"[Progress] {current}/{total} ({pct:.1f}%) {msg}")

def log_solver_success(logger: logging.Logger, idx: int, scaling_factor: float):
    """Log successful solver execution."""
    logger.debug(f"[Solver] Instance {idx}: Convergence OK, s={scaling_factor:.6f}")

def log_solver_failure(logger: logging.Logger, idx: int, reason: str):
    """Log solver failure."""
    logger.warning(f"[Solver] Instance {idx}: Failed - {reason}")

def log_numerical_warning(logger: logging.Logger, idx: int, warning: str):
    """Log numerical warnings."""
    logger.warning(f"[Numerical] Instance {idx}: {warning}")

def log_skipped_instance(logger: logging.Logger, idx: int, reason: str):
    """Log skipped instances."""
    logger.info(f"[Skip] Instance {idx}: {reason}")

def apply_epsilon_floor(value: float, epsilon: Optional[float] = None) -> float:
    """Apply epsilon floor to a value to prevent division by zero."""
    if epsilon is None:
        config = get_config()
        epsilon = getattr(config, 'EPSILON_FLOOR', 1e-6)
    return max(value, epsilon)

def safe_log(value: float, epsilon: Optional[float] = None) -> float:
    """Compute log safely, applying epsilon floor if value is non-positive."""
    safe_val = apply_epsilon_floor(value, epsilon)
    return np.log(safe_val)

def safe_divide(numerator: float, denominator: float, epsilon: Optional[float] = None) -> float:
    """Safely divide, applying epsilon floor to denominator."""
    safe_denom = apply_epsilon_floor(denominator, epsilon)
    return numerator / safe_denom

def check_numerical_stability(matrix: np.ndarray, logger: Optional[logging.Logger] = None) -> bool:
    """Check if a matrix is numerically stable (no NaNs or Infs)."""
    if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
        if logger:
            logger.warning("Numerical instability detected: NaN or Inf values present.")
        return False
    return True

def linear_drift(start: float, end: float, step: int, total_steps: int) -> float:
    """Compute linear drift value for a given step."""
    return start + (end - start) * (step / total_steps)

def exponential_drift(start: float, end: float, step: int, total_steps: int, rate: float = 1.0) -> float:
    """Compute exponential drift value for a given step."""
    if total_steps == 0:
        return start
    t = step / total_steps
    return start * np.exp(rate * t) + (end - start) * (1 - np.exp(-rate * t))

def sinusoidal_drift(start: float, end: float, step: int, total_steps: int, freq: float = 1.0) -> float:
    """Compute sinusoidal drift value for a given step."""
    if total_steps == 0:
        return start
    t = step / total_steps
    return start + (end - start) * (0.5 * (1 + np.sin(freq * np.pi * t - np.pi / 2)) + 0.5)

def get_drift_model(model_type: str):
    """Return the drift function based on type."""
    models = {
        'linear': linear_drift,
        'exponential': exponential_drift,
        'sinusoidal': sinusoidal_drift
    }
    if model_type not in models:
        raise ValueError(f"Unknown drift model type: {model_type}")
    return models[model_type]

def generate_epsilon_sweep_values() -> List[float]:
    """Generate a list of epsilon values for sensitivity analysis."""
    # Defined in config.py, but we can provide a default here if needed
    return [1e-8, 1e-6, 1e-4, 1e-2]

def compute_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_to_parquet(df: pd.DataFrame, path: Path):
    """Save DataFrame to Parquet format."""
    df.to_parquet(path, index=False)

def load_from_parquet(path: Path) -> pd.DataFrame:
    """Load DataFrame from Parquet format."""
    return pd.read_parquet(path)

def generate_checksum_for_dataset(csv_path: Path) -> str:
    """Generate checksum for the generated dataset CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    return compute_checksum(csv_path)

def save_checksum_to_file(checksum: str, csv_path: Path):
    """Save the checksum to a .sha256 file."""
    checksum_path = csv_path.with_suffix(csv_path.suffix + '.sha256')
    with open(checksum_path, 'w') as f:
        f.write(checksum)
    return checksum_path

def compute_and_store_checksums(csv_path: Path) -> Path:
    """Compute and store checksum for the generated dataset."""
    checksum = generate_checksum_for_dataset(csv_path)
    return save_checksum_to_file(checksum, csv_path)

def main():
    """Main entry point for utility tests (optional)."""
    pass
