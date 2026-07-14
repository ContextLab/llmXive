import os
import random
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Thresholds & Constants ---
PREVALENCE_THRESHOLD = 0.001  # 0.1%
RAREFACTION_LOSS_THRESHOLD = 0.20  # 20%
MIN_MEDIAN_DEPTH = 1000  # Minimum acceptable median sequencing depth
RANDOM_SEED = 42

# --- Paths ---
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_INTERIM_DIR = PROJECT_ROOT / "data" / "interim"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "plots"

# --- Helper Functions ---

def ensure_directories() -> None:
    """
    Creates all required project directories if they do not exist.
    """
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_INTERIM_DIR,
        RESULTS_DIR,
        FIGURES_DIR,
        PROJECT_ROOT / "code" / "models",
        PROJECT_ROOT / "code" / "utils",
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
        PROJECT_ROOT / "tests" / "contract",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def set_random_seed(seed: int = RANDOM_SEED) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, and python.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_output_path(subdir: str, filename: str) -> Path:
    """
    Constructs a full path for an output file within the data or results directory.
    
    Args:
        subdir: The subdirectory (e.g., 'processed', 'interim', 'plots')
        filename: The name of the file.
        
    Returns:
        Path: The absolute path to the file.
    """
    base_map = {
        'processed': DATA_PROCESSED_DIR,
        'interim': DATA_INTERIM_DIR,
        'plots': FIGURES_DIR,
        'raw': DATA_RAW_DIR
    }
    
    if subdir not in base_map:
        raise ValueError(f"Unknown output subdirectory: {subdir}. Options: {list(base_map.keys())}")
        
    return base_map[subdir] / filename

def calculate_median_depth(count_matrix: Union[np.ndarray, List[List[float]]]) -> float:
    """
    Calculates the median sequencing depth (median of non-zero column sums).
    
    Args:
        count_matrix: A 2D array-like object where rows are samples and columns are taxa.
                      Values represent read counts.
                      
    Returns:
        float: The median sequencing depth. Returns 0.0 if all samples have zero depth.
    """
    arr = np.asarray(count_matrix)
    if arr.size == 0:
        return 0.0
        
    # Sum counts across taxa (columns) for each sample (rows)
    # axis=1 sums across columns (taxa) to get depth per sample
    sample_depths = np.sum(arr, axis=1)
    
    # Filter out zero-depth samples to avoid skewing the median if empty samples exist
    non_zero_depths = sample_depths[sample_depths > 0]
    
    if len(non_zero_depths) == 0:
        return 0.0
        
    return float(np.median(non_zero_depths))

def estimate_rarefaction_loss(
    count_matrix: Union[np.ndarray, List[List[float]]], 
    target_depth: Optional[float] = None
) -> float:
    """
    Estimates the percentage of samples that would be lost if rarefied to a target depth.
    
    If target_depth is not provided, it defaults to the median sequencing depth.
    
    Args:
        count_matrix: A 2D array-like object (samples x taxa).
        target_depth: The depth to rarefy to. If None, uses median depth.
                      
    Returns:
        float: The fraction of samples (0.0 to 1.0) that would be lost (have depth < target).
    """
    arr = np.asarray(count_matrix)
    if arr.size == 0:
        return 0.0
        
    sample_depths = np.sum(arr, axis=1)
    
    if target_depth is None:
        target_depth = calculate_median_depth(arr)
        
    if target_depth <= 0:
        return 0.0
        
    # Count samples with depth strictly less than target
    lost_samples = np.sum(sample_depths < target_depth)
    total_samples = len(sample_depths)
    
    if total_samples == 0:
        return 0.0
        
    return float(lost_samples / total_samples)

# Initialize directories on module load if needed, or call explicitly
# ensure_directories() 
