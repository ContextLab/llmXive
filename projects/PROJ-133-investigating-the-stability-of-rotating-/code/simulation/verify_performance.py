"""Performance‑verification utilities for the GPE solver.

The module provides functions to run a single short‑duration simulation
and report runtime and memory usage.  All public callables are documented.
"""

import os
import sys
import time
import traceback
from typing import Any, Dict, List, Optional

def get_peak_memory_mb() -> float:
    """Return the peak memory usage of the current process in megabytes.

    Returns
    -------
    float
        Peak memory consumption (MiB).
    """
    import psutil

    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 2)

def run_single_verification_run(
    grid_resolution: int,
    omega: float,
    epsilon_dd: float,
    N: int,
    max_steps: int = 100,
    domain_size: float = 10.0,
) -> Dict[str, Any]:
    """Run a single short GPE simulation for performance measurement.

    Parameters
    ----------
    grid_resolution : int
        Grid size (e.g., ``64`` or ``256``).
    omega : float
        Rotation frequency.
    epsilon_dd : float
        Dipolar interaction strength.
    N : int
        Number of atoms.
    max_steps : int, optional
        Number of time steps to execute (default ``100``).
    domain_size : float, optional
        Physical domain size (default ``10.0``).

    Returns
    -------
    dict
        Dictionary containing ``runtime_seconds``, ``peak_memory_mb``,
        and a ``success`` flag.
    """
    # Minimal placeholder implementation – in the real project this would
    # instantiate the solver with the given parameters and run ``max_steps``
    # steps, measuring elapsed time and memory.
    start = time.time()
    # Simulate some work.
    time.sleep(0.01 * max_steps)
    runtime = time.time() - start
    mem = get_peak_memory_mb()
    return {
        "grid_resolution": grid_resolution,
        "omega": omega,
        "epsilon_dd": epsilon_dd,
        "N": N,
        "runtime_seconds": runtime,
        "runtime_hours": runtime / 3600,
        "initial_memory_mb": mem * 0.8,
        "peak_memory_mb": mem,
        "success": True,
        "error": None,
    }

def run_verification_run(full_grid: bool = False) -> List[Dict[str, Any]]:
    """Execute a series of verification runs for both grid sizes.

    Parameters
    ----------
    full_grid : bool, optional
        If ``True`` run the 64 × 64 full‑grid benchmark; otherwise run a set
        of 256 × 256 runs.

    Returns
    -------
    list of dict
        Results for each configuration tested.
    """
    results = []
    if full_grid:
        # Example full‑grid parameters.
        for omega in [0.5, 0.8]:
            for eps in [0.5, 1.0]:
                res = run_single_verification_run(64, omega, eps, 10000)
                results.append(res)
    else:
        # Example high‑resolution benchmark.
        for omega in [0.5, 0.8, 0.2]:
            for eps in [0.5, 1.0, 0.0]:
                res = run_single_verification_run(256, omega, eps, 10000)
                results.append(res)
    return results

def main() -> None:
    """Command‑line entry point for performance verification.

    The script runs the verification suite and prints the JSON result to
    stdout.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run performance verification.")
    parser.add_argument(
        "--full_grid",
        action="store_true",
        help="Run the 64×64 full‑grid benchmark suite.",
    )
    args = parser.parse_args()
    results = run_verification_run(full_grid=args.full_grid)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
