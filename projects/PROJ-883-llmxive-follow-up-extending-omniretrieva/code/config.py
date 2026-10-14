"""Configuration utilities."""

import os
from pathlib import Path

def get_config():
    """Return a dictionary with basic configuration.

    The configuration includes:
    - Random seed
    - Directory locations for raw / processed / results data
    - CPU throttling parameters (cores, memory limit, mode)
    """
    base_dir = Path(__file__).resolve().parents[1]
    return {
        "seed": int(os.getenv("SEED", "42")),
        "data_dir": base_dir / "data",
        "raw_dir": base_dir / "data" / "raw",
        "processed_dir": base_dir / "data" / "processed",
        "results_dir": base_dir / "data" / "results",
        # Throttling configuration (used by cpu_throttle utilities)
        "throttle_mode": os.getenv("THROTTLE_MODE", "cgroups"),  # or "time_only"
        "cpu_cores": int(os.getenv("CPU_CORES", "2")),
        "memory_gb": int(os.getenv("MEMORY_GB", "7")),
    }
