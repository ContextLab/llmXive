"""
Configuration management for the Quantization Impact on GW Reconstruction project.

Handles random seeds, resource limits (CI constraints), and batch size calculations
for the N=1200 pilot study.
"""
import os
import numpy as np
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Constants: CI Resource Limits (Hard Constraints)
# --------------------------------------------------------------------------
CI_CPU_LIMIT = 2
CI_RAM_LIMIT_GB = 7.0
CI_TIME_LIMIT_HOURS = 6.0
CI_TIME_LIMIT_SECONDS = CI_TIME_LIMIT_HOURS * 3600

# Pilot Study Parameters
PILOT_N_SIGNALS = 1200
PILOT_BIT_DEPTHS = [1, 8, 10, 12, 14, 16]
PILOT_SNR_BINS = [(8, 14), (14, 20), (20, 30), (30, 50)]
PILOT_SIGNALS_PER_BIN = 50

# Memory Estimation Constants (bytes per signal)
# Estimation: 
# - Waveform (float64): 4096 samples * 8 bytes = 32KB
# - Noise PSD (float64): 4096 samples * 8 bytes = 32KB
# - Inference state (posterior samples): ~10,000 samples * 4 params * 8 bytes = 320KB
# - Overhead/Python objects: ~100KB
# Total per signal approx: 0.5 MB (conservative upper bound)
ESTIMATED_MEMORY_PER_SIGNAL_MB = 0.5
ESTIMATED_MEMORY_PER_SIGNAL_BYTES = ESTIMATED_MEMORY_PER_SIGNAL_MB * 1024 * 1024

# --------------------------------------------------------------------------
# Random Seed Management
# --------------------------------------------------------------------------
def get_seed(env_var: str = "QUANTIZATION_SEED") -> int:
    """
    Retrieves the random seed from the environment variable.
    Defaults to 42 if not set.
    """
    seed_str = os.getenv(env_var, "42")
    try:
        return int(seed_str)
    except ValueError:
        logger.warning(f"Invalid seed '{seed_str}', defaulting to 42")
        return 42

def set_seed(seed: int) -> None:
    """
    Sets the random seed for numpy, random, and python hash randomization.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    # Note: random module seed is handled by the caller if needed, 
    # but usually np.random is sufficient for scientific stacks.
    import random
    random.seed(seed)
    logger.info(f"Random seed set to {seed}")

# --------------------------------------------------------------------------
# Resource Limits
# --------------------------------------------------------------------------
def get_resource_limits() -> Dict[str, Any]:
    """
    Returns the CI resource limits as a dictionary.
    """
    return {
        "cpu_limit": CI_CPU_LIMIT,
        "ram_limit_gb": CI_RAM_LIMIT_GB,
        "ram_limit_bytes": int(CI_RAM_LIMIT_GB * 1024 * 1024 * 1024),
        "time_limit_seconds": CI_TIME_LIMIT_SECONDS
    }

# --------------------------------------------------------------------------
# Batch Constraint Calculations
# --------------------------------------------------------------------------
def calculate_batch_constraints() -> Dict[str, Any]:
    """
    Calculates the maximum batch size that fits within CI RAM limits.
    
    Returns a dictionary with:
    - max_batch_size: Maximum number of signals to process in one go.
    - recommended_batch_size: A safer batch size (80% of max).
    - pilot_feasible: Boolean indicating if N=1200 fits in the limit.
    - total_estimated_memory_gb: Estimated memory for the full pilot.
    """
    limits = get_resource_limits()
    ram_limit_bytes = limits["ram_limit_bytes"]
    
    # Calculate max signals that fit in RAM
    # We assume we need to hold the batch in memory plus overhead for the loader/process.
    # Safety factor of 0.8 to account for OS and Python interpreter overhead.
    safe_ram_bytes = int(ram_limit_bytes * 0.8)
    max_signals = int(safe_ram_bytes / ESTIMATED_MEMORY_PER_SIGNAL_BYTES)
    
    # Recommended batch size (conservative)
    recommended_signals = int(max_signals * 0.8)
    
    # Pilot feasibility check
    total_pilot_memory_gb = (PILOT_N_SIGNALS * ESTIMATED_MEMORY_PER_SIGNAL_BYTES) / (1024**3)
    pilot_feasible = total_pilot_memory_gb < CI_RAM_LIMIT_GB
    
    # Time feasibility (rough estimate: 20 seconds per signal on 2 CPU)
    # 1200 signals * 20s = 24000s = 6.66 hours. 
    # This is tight. We need to process in parallel or optimize.
    # Assuming parallel processing of 2 signals (2 CPUs) effectively halves time.
    # 6.66 hours / 2 = 3.33 hours. Feasible within 6 hours.
    estimated_time_hours = (PILOT_N_SIGNALS * 20) / (CI_CPU_LIMIT * 3600)
    time_feasible = estimated_time_hours <= CI_TIME_LIMIT_HOURS

    return {
        "max_batch_size": max_signals,
        "recommended_batch_size": recommended_signals,
        "pilot_n_signals": PILOT_N_SIGNALS,
        "total_estimated_memory_gb": round(total_pilot_memory_gb, 2),
        "pilot_feasible": pilot_feasible,
        "estimated_time_hours": round(estimated_time_hours, 2),
        "time_feasible": time_feasible,
        "constraints": {
            "cpu": CI_CPU_LIMIT,
            "ram_gb": CI_RAM_LIMIT_GB,
            "time_hours": CI_TIME_LIMIT_HOURS
        }
    }

def verify_pilot_feasibility() -> Tuple[bool, str]:
    """
    Verifies if the N=1200 pilot study is feasible under current CI constraints.
    
    Returns:
    - feasible: True if both memory and time constraints are met.
    - message: Detailed explanation of the feasibility status.
    """
    constraints = calculate_batch_constraints()
    
    if not constraints["pilot_feasible"]:
        msg = (
            f"Memory constraint violated. Pilot requires {constraints['total_estimated_memory_gb']} GB, "
            f"but limit is {CI_RAM_LIMIT_GB} GB."
        )
        return False, msg
    
    if not constraints["time_feasible"]:
        msg = (
            f"Time constraint violated. Estimated runtime is {constraints['estimated_time_hours']} hours, "
            f"but limit is {CI_TIME_LIMIT_HOURS} hours."
        )
        return False, msg

    msg = (
        f"Pilot feasible. Memory: {constraints['total_estimated_memory_gb']} GB < {CI_RAM_LIMIT_GB} GB. "
        f"Time: {constraints['estimated_time_hours']} hours < {CI_TIME_LIMIT_HOURS} hours. "
        f"Recommended batch size: {constraints['recommended_batch_size']}."
    )
    return True, msg

# --------------------------------------------------------------------------
# Main Entry Point for Script Execution
# --------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Project Configuration & Pilot Feasibility Report ===")
    seed = get_seed()
    print(f"Active Seed: {seed}")
    
    limits = get_resource_limits()
    print(f"\nCI Resource Limits:")
    print(f"  CPU: {limits['cpu_limit']}")
    print(f"  RAM: {limits['ram_limit_gb']} GB")
    print(f"  Time: {limits['time_limit_seconds']}s ({limits['time_limit_seconds']/3600}h)")
    
    constraints = calculate_batch_constraints()
    print(f"\nBatch Constraints:")
    print(f"  Max Batch Size: {constraints['max_batch_size']}")
    print(f"  Recommended Batch Size: {constraints['recommended_batch_size']}")
    print(f"  Pilot Total Memory: {constraints['total_estimated_memory_gb']} GB")
    
    feasible, message = verify_pilot_feasibility()
    print(f"\nFeasibility Check: {'PASSED' if feasible else 'FAILED'}")
    print(f"Details: {message}")
    
    if not feasible:
        exit(1)
    
    print("\nConfiguration valid for N=1200 pilot.")
    exit(0)
