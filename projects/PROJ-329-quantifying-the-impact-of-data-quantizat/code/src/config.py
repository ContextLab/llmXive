import os
import numpy as np
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import json

# Resource Limits (CI Constraints)
CI_CPU_LIMIT = 2
CI_RAM_LIMIT_GB = 7.0
CI_TIME_LIMIT_HOURS = 6.0
CI_TIME_LIMIT_SECONDS = CI_TIME_LIMIT_HOURS * 3600

# Pilot Configuration
PILOT_N_SIGNALS = 1200
BIT_DEPTHS = [1, 8, 10, 12, 14, 16]
SNR_BINS = [
    (8, 14),
    (14, 20),
    (20, 30),
    (30, 50)
]
SIGNALS_PER_BIN = 50

# Memory Estimates (Conservative)
# Estimated memory per signal in MB (waveform + noise + inference overhead)
# Based on typical GW analysis workloads: ~15MB per signal for full inference context
MEMORY_PER_SIGNAL_MB = 15.0

def get_seed(seed_str: Optional[str] = None) -> int:
    """Get random seed from environment or default."""
    if seed_str:
        return int(seed_str)
    env_seed = os.getenv("RANDOM_SEED")
    if env_seed:
        return int(env_seed)
    return 42

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    os.environ["RANDOM_SEED"] = str(seed)
    np.random.seed(seed)

def get_resource_limits() -> Dict[str, float]:
    """Return current resource limits."""
    return {
        "cpu": CI_CPU_LIMIT,
        "ram_gb": CI_RAM_LIMIT_GB,
        "time_seconds": CI_TIME_LIMIT_SECONDS
    }

def calculate_batch_constraints() -> Dict[str, Any]:
    """
    Calculate batch size constraints based on resource limits.
    Returns a dictionary with memory and time feasibility analysis.
    """
    limits = get_resource_limits()
    
    # Memory calculation
    total_memory_needed_mb = PILOT_N_SIGNALS * MEMORY_PER_SIGNAL_MB
    total_memory_needed_gb = total_memory_needed_mb / 1024.0
    
    memory_feasible = total_memory_needed_gb <= limits["ram_gb"]
    
    # Time estimation (conservative)
    # Assume ~2 minutes per signal on 1 CPU for full inference
    # With 2 CPUs, parallelization factor ~1.8 (overhead)
    TIME_PER_SIGNAL_SECONDS = 120.0
    parallel_factor = 1.8
    estimated_time_seconds = (PILOT_N_SIGNALS * TIME_PER_SIGNAL_SECONDS) / parallel_factor
    estimated_time_hours = estimated_time_seconds / 3600.0
    
    time_feasible = estimated_time_seconds <= limits["time_seconds"]
    
    return {
        "pilot_n": PILOT_N_SIGNALS,
        "bit_depths": BIT_DEPTHS,
        "snr_bins": SNR_BINS,
        "signals_per_bin": SIGNALS_PER_BIN,
        "memory_needed_gb": total_memory_needed_gb,
        "memory_limit_gb": limits["ram_gb"],
        "memory_feasible": memory_feasible,
        "estimated_time_hours": estimated_time_hours,
        "time_limit_hours": limits["time_seconds"] / 3600.0,
        "time_feasible": time_feasible,
        "overall_feasible": memory_feasible and time_feasible
    }

def verify_pilot_feasibility() -> Tuple[bool, str]:
    """
    Verify if the pilot batch fits within CI constraints.
    Returns (feasible, message).
    """
    constraints = calculate_batch_constraints()
    
    if not constraints["overall_feasible"]:
        reasons = []
        if not constraints["memory_feasible"]:
            reasons.append(
                f"Memory: {constraints['memory_needed_gb']:.2f} GB exceeds limit {constraints['memory_limit_gb']} GB"
            )
        if not constraints["time_feasible"]:
            reasons.append(
                f"Time: {constraints['estimated_time_hours']:.2f} hours exceeds limit {constraints['time_limit_hours']} hours"
            )
        return False, "; ".join(reasons)
    
    return True, (
        f"Pilot N={PILOT_N_SIGNALS} feasible. "
        f"Memory: {constraints['memory_needed_gb']:.2f} GB / {constraints['memory_limit_gb']} GB. "
        f"Time: {constraints['estimated_time_hours']:.2f}h / {constraints['time_limit_hours']}h."
    )
