"""
Environment configuration for random seeds and CI resource limits.

This module defines constants for reproducibility (random seeds) and
resource constraints (CPU, RAM) to ensure the N=1200 pilot batch
fits within the 6-hour CI window and 7 GB RAM limit.
"""
import os
import numpy as np
from typing import Tuple, Dict, Any
from pathlib import Path

# --- Random Seed Configuration ---
# Base seed for reproducibility. Can be overridden by environment variable.
BASE_SEED = int(os.getenv("GW_QUANTIZATION_SEED", "42"))

# Number of independent runs for statistical validation (US3)
NUM_INDEPENDENT_RUNS = 10

# --- CI Resource Limits ---
# Maximum CPU cores allowed (per CI configuration)
MAX_CPU_CORES = 2

# Maximum RAM in GB allowed (per CI configuration)
MAX_RAM_GB = 7.0
MAX_RAM_BYTES = int(MAX_RAM_GB * 1024 ** 3)

# --- Pilot Batch Constraints ---
# Total number of signals in the pilot batch
# 6 depths (1, 8, 10, 12, 14, 16) * 4 SNR bins * 50 signals = 1200
TOTAL_PILOT_SIGNALS = 1200

# Bit depths to simulate
BIT_DEPTHS = [1, 8, 10, 12, 14, 16]

# SNR Bins (lower, upper)
SNR_BINS = [(8, 14), (14, 20), (20, 30), (30, 50)]

# Signals per bin per depth
SIGNALS_PER_BIN = 50

# --- Memory Estimation Constants ---
# Approximate memory footprint per signal in MB (float64 waveform + metadata + overhead)
# Based on: 4096 samples * 8 bytes * 2 (real/imag) + overhead ~ 64KB per signal
# Heuristic: 1MB per signal to be safe for processing buffers
MEM_PER_SIGNAL_MB = 1.0
MEM_PER_SIGNAL_BYTES = int(MEM_PER_SIGNAL_MB * 1024 ** 2)

# --- Derived Constraints ---
# Calculate maximum batch size that fits in RAM
# We reserve 2GB for OS/Python overhead, leaving 5GB for data
RESERVED_RAM_GB = 2.0
AVAILABLE_RAM_GB = MAX_RAM_GB - RESERVED_RAM_GB
AVAILABLE_RAM_BYTES = int(AVAILABLE_RAM_GB * 1024 ** 3)

MAX_BATCH_SIZE = AVAILABLE_RAM_BYTES // MEM_PER_SIGNAL_BYTES

# --- Time Constraints ---
# Total time budget in seconds (6 hours)
TOTAL_TIME_SECONDS = 6 * 3600

# Estimated time per signal in seconds (conservative estimate for inference)
# Inference (Bilby/PyCBC) can take 10-60s per signal depending on complexity.
# We assume 15s average for pilot estimation.
EST_TIME_PER_SIGNAL_SECONDS = 15

# Calculate max signals by time
MAX_SIGNALS_BY_TIME = TOTAL_TIME_SECONDS // EST_TIME_PER_SIGNAL_SECONDS

# --- Final Constraint ---
# The effective batch size is the minimum of RAM and Time constraints
# For N=1200 pilot, we must ensure 1200 <= MAX_BATCH_SIZE and 1200 <= MAX_SIGNALS_BY_TIME
# If not, we must chunk the processing.
SAFE_BATCH_SIZE = min(MAX_BATCH_SIZE, MAX_SIGNALS_BY_TIME)

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
CODE_DIR = PROJECT_ROOT / "code"
LOGS_DIR = PROJECT_ROOT / "logs"

def get_seed() -> int:
    """Return the current random seed."""
    return BASE_SEED

def set_seed(seed: int) -> None:
    """Set the random seed for numpy and python random."""
    global BASE_SEED
    BASE_SEED = seed
    np.random.seed(seed)
    try:
        import random
        random.seed(seed)
    except ImportError:
        pass

def get_resource_limits() -> Dict[str, Any]:
    """Return a dictionary of resource constraints."""
    return {
        "max_cpu": MAX_CPU_CORES,
        "max_ram_gb": MAX_RAM_GB,
        "max_batch_size": SAFE_BATCH_SIZE,
        "total_signals": TOTAL_PILOT_SIGNALS,
        "bit_depths": BIT_DEPTHS,
        "snr_bins": SNR_BINS,
        "signals_per_bin": SIGNALS_PER_BIN
    }

def calculate_batch_constraints() -> Tuple[int, int]:
    """
    Calculate the maximum number of signals that can be processed
    in a single batch given RAM and Time constraints.
    
    Returns:
        Tuple of (max_by_ram, max_by_time)
    """
    return (MAX_BATCH_SIZE, MAX_SIGNALS_BY_TIME)

def verify_pilot_feasibility() -> bool:
    """
    Verify if the N=1200 pilot batch is feasible within constraints.
    
    Returns:
        True if feasible, False otherwise.
    """
    feasible_ram = TOTAL_PILOT_SIGNALS <= MAX_BATCH_SIZE
    feasible_time = TOTAL_PILOT_SIGNALS <= MAX_SIGNALS_BY_TIME
    return feasible_ram and feasible_time