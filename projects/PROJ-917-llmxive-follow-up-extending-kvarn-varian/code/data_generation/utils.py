import numpy as np
from typing import Union, Optional, Callable, List
import json
import hashlib
from pathlib import Path
import logging
import os

# Configure logger
logger = logging.getLogger(__name__)

def apply_epsilon_floor(value: float, epsilon: float) -> float:
    """
    Applies an epsilon floor to a value to ensure numerical stability.
    Returns max(value, epsilon).
    """
    if not isinstance(value, (int, float, np.floating)):
        raise TypeError(f"Value must be a number, got {type(value)}")
    if not isinstance(epsilon, (int, float, np.floating)):
        raise TypeError(f"Epsilon must be a number, got {type(epsilon)}")
    
    return float(max(float(value), float(epsilon)))

def safe_log(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Computes logarithm safely, replacing non-positive values with a small epsilon.
    """
    if isinstance(x, np.ndarray):
        result = np.log(x, where=x > 0)
        result = np.where(x <= 0, np.log(1e-10), result)
        return result
    else:
        return np.log(x) if x > 0 else np.log(1e-10)

def safe_divide(numerator: Union[float, np.ndarray], denominator: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Performs division safely, handling division by zero.
    Returns 0.0 if denominator is 0.
    """
    if isinstance(denominator, np.ndarray):
        with np.errstate(divide='ignore', invalid='ignore'):
            result = numerator / denominator
            result = np.where(denominator == 0, 0.0, result)
            result = np.where(~np.isfinite(result), 0.0, result)
        return result
    else:
        if denominator == 0 or not np.isfinite(denominator):
            return 0.0
        res = numerator / denominator
        return res if np.isfinite(res) else 0.0

def check_numerical_stability(value: Union[float, np.ndarray], name: str = "value") -> bool:
    """
    Checks if a value is numerically stable (finite and not NaN).
    Returns True if stable, False otherwise.
    """
    if isinstance(value, np.ndarray):
        return bool(np.all(np.isfinite(value)))
    return bool(np.isfinite(value))

def linear_drift(x: float, slope: float, intercept: float) -> float:
    """
    Computes linear drift: y = slope * x + intercept
    """
    return slope * x + intercept

def exponential_drift(x: float, base: float, rate: float) -> float:
    """
    Computes exponential drift: y = base * exp(rate * x)
    """
    return base * np.exp(rate * x)

def sinusoidal_drift(x: float, amplitude: float, frequency: float, phase: float) -> float:
    """
    Computes sinusoidal drift: y = amplitude * sin(frequency * x + phase)
    """
    return amplitude * np.sin(frequency * x + phase)

def get_drift_model(model_type: str):
    """
    Returns the appropriate drift function based on model_type string.
    Supported: 'linear', 'exponential', 'sinusoidal'
    """
    if model_type == 'linear':
        return linear_drift
    elif model_type == 'exponential':
        return exponential_drift
    elif model_type == 'sinusoidal':
        return sinusoidal_drift
    else:
        raise ValueError(f"Unknown drift model type: {model_type}. Supported: linear, exponential, sinusoidal")

def generate_epsilon_sweep_values() -> List[float]:
    """
    Generates a list of epsilon values for sensitivity analysis.
    Returns a list of floats spanning a range from negligible to substantial.
    """
    # Fixed list as per task T005b and spec requirements
    return [1e-9, 1e-6, 1e-3]

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 checksum of a file.
    Raises FileNotFoundError if the file does not exist.
    Raises IOError if the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {path}: {e}")

def save_json_with_checksum(data: dict, output_path: Union[str, Path]) -> None:
    """
    Saves data to a JSON file and computes its checksum.
    The checksum is stored in the same directory with a .sha256 extension.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    json_str = json.dumps(data, indent=2, sort_keys=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    checksum = compute_checksum(path)
    checksum_path = path.with_suffix(path.suffix + '.sha256')
    
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(checksum)
    
    logger.info(f"Saved {path} with checksum {checksum}")

def compute_and_store_checksums(data_dir: Union[str, Path], output_dir: Union[str, Path]) -> dict:
    """
    Computes SHA-256 checksums for all files in the specified data_dir
    and stores the results in a JSON map at output_dir/checksums.json.
    
    Args:
        data_dir: Path to the directory to scan for files.
        output_dir: Path to the directory where checksums.json will be saved.
    
    Returns:
        A dictionary mapping relative file paths to their SHA-256 checksums.
    """
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")
    
    if not data_path.is_dir():
        raise NotADirectoryError(f"Data path is not a directory: {data_path}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    
    logger.info(f"Computing checksums for all files in {data_path}...")
    
    for file_path in sorted(data_path.rglob('*')):
        if file_path.is_file():
            rel_path = file_path.relative_to(data_path)
            try:
                checksum = compute_checksum(file_path)
                checksums[str(rel_path)] = checksum
                logger.debug(f"Computed checksum for {rel_path}: {checksum[:16]}...")
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Skipping file {rel_path} due to error: {e}")
    
    output_file = output_path / "checksums.json"
    save_json_with_checksum(checksums, output_file)
    
    logger.info(f"Checksums saved to {output_file}. Total files processed: {len(checksums)}")
    return checksums