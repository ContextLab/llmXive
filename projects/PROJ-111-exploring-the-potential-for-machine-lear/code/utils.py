import numpy as np
from typing import List, Tuple, Dict, Optional
import warnings
import os
import hashlib
from pathlib import Path

def calculate_autocorrelation_time(series: np.ndarray) -> float:
    """Calculates the integrated autocorrelation time of a series using the Madras-Sokal windowing method."""
    if len(series) < 2:
        return 0.0
    
    # Normalize the series
    mean = np.mean(series)
    var = np.var(series)
    if var == 0:
        return 0.0
    
    series_centered = series - mean
    
    # Calculate autocorrelation
    n = len(series)
    autocorr = np.correlate(series_centered, series_centered, mode='full')
    autocorr = autocorr[n-1:] / (var * n)
    
    # Madras-Sokal windowing
    window_size = int(np.ceil(2 * np.sqrt(n)))
    window_size = min(window_size, n // 2)
    
    tau_int = 0.0
    for t in range(1, window_size):
        tau_int += autocorr[t]
        # Stop if autocorrelation becomes negligible
        if abs(autocorr[t]) < 0.01:
            break
    
    return 2.0 * tau_int

def thin_dataset(series: np.ndarray, thinning_factor: int) -> np.ndarray:
    """Thins a dataset by a given factor (must be >= 2 * tau_int)."""
    if thinning_factor <= 0:
        raise ValueError("Thinning factor must be greater than zero.")
    return series[::thinning_factor]

def calculate_magnetic_susceptibility(spins: np.ndarray) -> float:
    """
    Calculates the magnetic susceptibility for a spin configuration.
    Chi = (1/N) * ( <M^2> - <|M|>^2 )
    """
    if spins.ndim == 1:
        # 1D array: treat as single configuration
        m = np.sum(spins)
        n = spins.size
        return (m**2 - abs(m)**2) / n
    
    elif spins.ndim == 4:
        # Expected shape: (batch, 3, L, L) for Heisenberg
        # Compute magnetization per sample
        mags = np.linalg.norm(np.sum(spins, axis=(2, 3)), axis=1)
        mags_sq = np.sum(spins, axis=(2, 3))
        mags_sq = np.sum(mags_sq**2, axis=1)
        
        n = spins.shape[0]
        mean_m_sq = np.mean(mags_sq)
        mean_abs_m = np.mean(mags)
        
        return (mean_m_sq - mean_abs_m**2) / (spins.shape[2] * spins.shape[3])
    
    else:
        raise ValueError(f"Unsupported spins shape: {spins.shape}")

def perform_finite_size_scaling(data: List[float], lattice_sizes: List[int]) -> float:
    """Performs finite-size scaling to extrapolate T* to the thermodynamic limit."""
    if len(data) != len(lattice_sizes):
        raise ValueError("Data and lattice sizes lists must have the same length.")
    if len(data) < 2:
        raise ValueError("Need at least 2 lattice sizes for FSS.")

    from scipy import stats
    log_l = np.log(lattice_sizes)
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_l, data)
    
    # Extrapolate to infinite size (L -> infinity)
    # T*(L) = T_c + a * L^(-1/nu)
    # As L -> inf, T*(L) -> T_c
    t_star = intercept 
    return t_star

def find_peak_temperature(variance_data: List[float], temperatures: List[float]) -> float:
    """Finds the peak temperature in a variance curve."""
    if len(variance_data) != len(temperatures):
        raise ValueError("Variance data and temperatures lists must have the same length.")

    peak_index = np.argmax(variance_data)
    return temperatures[peak_index]

def calculate_latent_variance(latent_vectors: List[np.ndarray]) -> float:
    """Calculates the total latent variance."""
    total_variance = 0.0
    for vector in latent_vectors:
        total_variance += np.var(vector)
    return total_variance

def compute_file_checksum(filepath: str) -> str:
    """Computes SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_checksums(data_dirs: Optional[List[str]] = None, output_path: str = "data/checksums.txt") -> None:
    """
    Generates checksums.txt for all files in specified data directories.
    Default dirs: ['data/raw', 'data/processed']
    
    Format: <sha256>  <relative_path>
    """
    if data_dirs is None:
        data_dirs = ['data/raw', 'data/processed']
    
    checksums = []
    
    for directory in data_dirs:
        dir_path = Path(directory)
        if not dir_path.exists():
            warnings.warn(f"Directory {directory} does not exist, skipping.")
            continue
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                # Use relative path from project root
                rel_path = file_path.relative_to(Path.cwd())
                checksum = compute_file_checksum(str(file_path))
                checksums.append(f"{checksum}  {rel_path}")
    
    # Sort for deterministic output
    checksums.sort(key=lambda x: x.split('  ')[1])
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(checksums))
        if checksums:
            f.write('\n')

def verify_checksums(checksum_file: str = "data/checksums.txt") -> bool:
    """
    Verifies checksums of files against checksums.txt.
    Returns True if all files match, False otherwise.
    Raises RuntimeError on mismatch or missing file.
    """
    if not os.path.exists(checksum_file):
        raise RuntimeError(f"Checksum file {checksum_file} not found.")
    
    with open(checksum_file, 'r') as f:
        lines = f.readlines()
    
    if not lines:
        warnings.warn("Checksum file is empty.")
        return True
    
    all_valid = True
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('  ')
        if len(parts) != 2:
            raise RuntimeError(f"Invalid checksum line format: {line}")
        
        expected_checksum, rel_path = parts
        file_path = Path(rel_path)
        
        if not file_path.exists():
            raise RuntimeError(f"File missing during verification: {rel_path}")
        
        actual_checksum = compute_file_checksum(str(file_path))
        
        if actual_checksum != expected_checksum:
            raise RuntimeError(f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}")
    
    return all_valid
