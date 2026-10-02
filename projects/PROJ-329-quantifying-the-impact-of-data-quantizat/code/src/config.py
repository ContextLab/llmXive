import os
import numpy as np
from typing import Tuple, Dict, Any, Optional
from pathlib import Path
import json
import logging

# Resource constraints from T009
CI_TIME_LIMIT_HOURS = 6
CI_MEMORY_LIMIT_GB = 7
CPU_CORES_AVAILABLE = 2

# Pilot configuration
NUM_BIT_DEPTHS = 6  # 1, 8, 10, 12, 14, 16
NUM_SNR_BINS = 4    # 8-14, 14-20, 20-30, 30-50
SIGNALS_PER_BIN = 50
TOTAL_PILOT_SIGNALS = NUM_BIT_DEPTHS * NUM_SNR_BINS * SIGNALS_PER_BIN

# Estimated costs per signal (empirical approximations for BBH IMRPhenomPv)
# In seconds (generation + injection + quantization)
ESTIMATE_GEN_TIME_PER_SIGNAL_SEC = 0.5
# In seconds (MCMC inference: 500 steps, 2 walkers, uniform prior)
ESTIMATE_INF_TIME_PER_SIGNAL_SEC = 45.0
# In GB (HDF5 waveform + metadata + posterior samples)
ESTIMATE_MEM_PER_SIGNAL_GB = 0.005  # ~5 MB per signal in memory during processing

# Derived constraints
TOTAL_ESTIMATED_GEN_TIME_SEC = TOTAL_PILOT_SIGNALS * ESTIMATE_GEN_TIME_PER_SIGNAL_SEC
TOTAL_ESTIMATED_INF_TIME_SEC = TOTAL_PILOT_SIGNALS * ESTIMATE_INF_TIME_PER_SIGNAL_SEC
TOTAL_ESTIMATED_MEM_GB = TOTAL_PILOT_SIGNALS * ESTIMATE_MEM_PER_SIGNAL_GB

# Batch size constraints
MAX_BATCH_SIZE_BY_TIME = int((CI_TIME_LIMIT_HOURS * 3600) / ESTIMATE_INF_TIME_PER_SIGNAL_SEC)
MAX_BATCH_SIZE_BY_MEM = int(CI_MEMORY_LIMIT_GB / ESTIMATE_MEM_PER_SIGNAL_GB)
MAX_BATCH_SIZE = min(MAX_BATCH_SIZE_BY_TIME, MAX_BATCH_SIZE_BY_MEM)

# Seed management
DEFAULT_SEED = 42

def get_seed() -> int:
    """Retrieve the random seed from environment or use default."""
    return int(os.environ.get("GW_QUANT_SEED", DEFAULT_SEED))

def set_seed(seed: int) -> None:
    """Set the random seed for reproducibility."""
    os.environ["GW_QUANT_SEED"] = str(seed)
    np.random.seed(seed)
    import random
    random.seed(seed)

def get_resource_limits() -> Dict[str, Any]:
    """Return resource limits dictionary."""
    return {
        "time_limit_hours": CI_TIME_LIMIT_HOURS,
        "memory_limit_gb": CI_MEMORY_LIMIT_GB,
        "cpu_cores": CPU_CORES_AVAILABLE
    }

def calculate_batch_constraints() -> Dict[str, Any]:
    """Calculate and return batch size constraints."""
    return {
        "total_pilot_signals": TOTAL_PILOT_SIGNALS,
        "max_batch_size_by_time": MAX_BATCH_SIZE_BY_TIME,
        "max_batch_size_by_mem": MAX_BATCH_SIZE_BY_MEM,
        "max_batch_size": MAX_BATCH_SIZE,
        "estimated_total_gen_time_hours": TOTAL_ESTIMATED_GEN_TIME_SEC / 3600,
        "estimated_total_inf_time_hours": TOTAL_ESTIMATED_INF_TIME_SEC / 3600,
        "estimated_total_mem_gb": TOTAL_ESTIMATED_MEM_GB
    }

def verify_pilot_feasibility() -> Tuple[bool, str]:
    """
    Verify if the pilot batch (N=1200) fits within CI limits.
    Returns (is_feasible, reason_message).
    """
    constraints = calculate_batch_constraints()
    is_feasible = True
    reasons = []

    # Check memory
    if constraints["estimated_total_mem_gb"] > CI_MEMORY_LIMIT_GB:
        is_feasible = False
        reasons.append(f"Memory {constraints['estimated_total_mem_gb']:.2f} GB > {CI_MEMORY_LIMIT_GB} GB limit")

    # Check time
    if constraints["estimated_total_inf_time_hours"] > CI_TIME_LIMIT_HOURS:
        is_feasible = False
        reasons.append(f"Inference time {constraints['estimated_total_inf_time_hours']:.2f}h > {CI_TIME_LIMIT_HOURS}h limit")

    if is_feasible:
        msg = (
            f"Pilot N={TOTAL_PILOT_SIGNALS} is feasible. "
            f"Est. Time: {constraints['estimated_total_inf_time_hours']:.2f}h, "
            f"Est. Mem: {constraints['estimated_total_mem_gb']:.2f} GB. "
            f"Max batch size allowed: {MAX_BATCH_SIZE}."
        )
    else:
        msg = "; ".join(reasons)

    return is_feasible, msg
