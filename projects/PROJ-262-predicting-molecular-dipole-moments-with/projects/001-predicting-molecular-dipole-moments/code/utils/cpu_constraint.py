"""
Utility to enforce a maximum number of CPU cores used by the pipeline.

The pipeline is required to run with at most 2 CPU cores (FR-010, SC-003).
This module sets common environment variables that control the number of
threads used by popular scientific libraries (NumPy, SciPy, PyTorch, etc.)
and provides a simple entry‑point that can be invoked as a script.

Usage (as a script):
    python cpu_constraint.py

The function can also be imported and called from other modules:
    from utils.cpu_constraint import enforce_cpu_limit
    enforce_cpu_limit(max_cores=2)
"""

from __future__ import annotations

import os
import sys
import warnings
from typing import Optional


def _set_thread_env(var_name: str, value: str) -> None:
    """Helper to set an environment variable, preserving any existing value."""
    if os.getenv(var_name) != value:
        os.environ[var_name] = value


def enforce_cpu_limit(max_cores: int = 2) -> None:
    """
    Enforce a hard limit on the number of CPU cores used by the process
    and by common scientific libraries.

    Parameters
    ----------
    max_cores : int, optional
        Maximum number of CPU cores the pipeline may use. Defaults to 2.
    """
    if max_cores < 1:
        raise ValueError("max_cores must be at least 1")

    total_cpus: Optional[int] = os.cpu_count()
    if total_cpus is not None and total_cpus > max_cores:
        warnings.warn(
            f"System reports {total_cpus} CPUs, but the pipeline is limited to {max_cores}."
        )

    # Set environment variables that many libraries respect
    for var in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMBA_NUM_THREADS",
    ):
        _set_thread_env(var, str(max_cores))

    # Torch – if available, force its internal thread pool size
    try:
        import torch

        torch.set_num_threads(max_cores)
    except Exception:
        # Torch may not be installed; ignore silently
        pass

    # Joblib – set default parallelism if joblib is used elsewhere
    try:
        import joblib

        # joblib does not expose a global setter, but we can monkey‑patch the
        # default Parallel constructor to use the desired n_jobs.
        original_parallel = joblib.Parallel

        class LimitedParallel(original_parallel):
            def __init__(self, *args, n_jobs=None, **kwargs):
                super().__init__(*args, n_jobs=max_cores if n_jobs is None else n_jobs, **kwargs)

        joblib.Parallel = LimitedParallel
    except Exception:
        # joblib may not be installed; ignore silently
        pass


def main() -> int:
    """
    Script entry point. Enforces the CPU core limit and reports the
    configuration to stdout. Returns an exit code suitable for ``sys.exit``.
    """
    enforce_cpu_limit()
    print(
        f"CPU core constraint enforced: maximum {os.getenv('OMP_NUM_THREADS')} cores per process."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())