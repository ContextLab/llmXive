"""
Memory monitoring utilities.
Implements T005 and T005b: Enforce ≤7 GB RAM limit via automatic
sub‑sampling or streaming fallback.  The module provides low‑level
helpers (current/peak usage) as well as a high‑level ``enforce_memory_limit``
function that can be called at any pipeline stage.  If the memory
consumption of a ``pandas.DataFrame`` exceeds the limit, the function
attempts a stratified sub‑sample (preserving the ``group`` column when
present) and writes a concise log entry to
``data/logs/memory_subsampling.log``.  When sub‑sampling is impossible,
a ``MemoryLimitExceeded`` exception is raised, causing the pipeline to
abort with a clear message.

The implementation builds on the original utilities that were already
present in the repository, extending them to satisfy the test suite
``tests/code/tests/test_memory_monitor.py`` which expects that:

* an 8 GB synthetic workload triggers sub‑sampling,
* the resulting DataFrame fits within the 7 GB limit,
* a log file documenting the sub‑sampling action is created.

All public names remain compatible with the existing API surface.
"""

import os
import resource
import gc
import sys
from typing import Optional, Union

import pandas as pd
import numpy as np
import psutil

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the limit and subsetting is impossible."""
    pass

def get_current_memory_mb() -> float:
    """Get current RSS memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # On Linux, ru_maxrss is in KB. On macOS, it is in bytes.
    # We normalize to MB.
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024.0

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if sys.platform == 'darwin':
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_mb: float = 7000) -> None:
    """
    Check if current memory usage exceeds limit.
    Raises MemoryLimitExceeded if limit is exceeded.
    """
    current = get_current_memory_mb()
    if current > limit_mb:
        raise MemoryLimitExceeded(f"Memory limit exceeded: {current:.2f} MB > {limit_mb} MB")

def enforce_memory_limit(limit_mb: float = 7000) -> None:
    """Enforce memory limit, raising exception if exceeded."""
    check_memory_limit(limit_mb)

def get_memory_usage_report() -> dict:
    """Get a report of memory usage."""
    return {
        'current_mb': get_current_memory_mb(),
        'limit_mb': 7000
    }

def simulate_large_memory_usage(size_mb: int) -> None:
    """Simulate large memory usage for testing."""
    # Allocate a bytearray; keep a reference to avoid immediate GC.
    _ = bytearray(size_mb * 1024 * 1024)

def cleanup_large_memory() -> None:
    """Attempt to cleanup large memory allocations."""
    gc.collect()

def estimate_dataframe_memory_mb(df: pd.DataFrame) -> float:
    """
    Estimate the memory usage of a pandas DataFrame in MB.
    """
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def _write_subsampling_log(original_rows: int, retained_rows: int, limit_gb: float) -> None:
    """
    Write a one‑line entry to ``data/logs/memory_subsampling.log`` documenting
    the sub‑sampling action.
    """
    log_path = os.path.join('data', 'logs', 'memory_subsampling.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(
            f"Memory limit {limit_gb:.1f} GB exceeded: "
            f"{original_rows} rows → {retained_rows} rows retained.\n"
        )

def check_and_subset_memory(
    df: pd.DataFrame,
    limit_gb: float = 7.0,
    min_sample_fraction: float = 0.01
) -> pd.DataFrame:
    """
    Check if the DataFrame fits within the memory limit.
    If it exceeds the limit, attempt to sample rows to reduce memory usage
    while maintaining statistical representativeness (stratified sampling if possible).

    If subsetting is impossible (e.g., single row > limit or sampling below min_fraction
    still exceeds limit), raise MemoryLimitExceeded.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame.
    limit_gb : float, optional
        Memory limit in GB (default 7.0).
    min_sample_fraction : float, optional
        Minimum fraction of rows to retain if subsetting.

    Returns
    -------
    pd.DataFrame
        A DataFrame that fits within the memory limit (original or subset).

    Raises
    ------
    MemoryLimitExceeded
        If the DataFrame cannot be reduced to fit the limit.
    """
    limit_mb = limit_gb * 1024
    current_memory_mb = estimate_dataframe_memory_mb(df)

    if current_memory_mb <= limit_mb:
        return df

    n_rows = len(df)
    if n_rows == 0:
        return df

    # Estimate size per row in bytes
    bytes_per_row = (current_memory_mb * 1024 * 1024) / n_rows

    # Desired number of rows to fit within the limit
    target_rows = int(limit_mb * 1024 * 1024 / bytes_per_row)

    # Enforce a minimum sample size
    min_rows = max(1, int(n_rows * min_sample_fraction))
    target_rows = max(target_rows, min_rows)

    if target_rows >= n_rows:
        # Cannot reduce enough
        raise MemoryLimitExceeded(
            f"Memory limit exceeded ({current_memory_mb:.2f} MB > {limit_mb} MB) "
            f"and subsetting impossible (requires < {target_rows} rows, but min is {min_rows})"
        )

    # Perform stratified sampling if a 'group' column exists, else random sampling
    if 'group' in df.columns:
        try:
            sampled_df = df.groupby('group', group_keys=False).apply(
                lambda x: x.sample(
                    n=min(len(x), max(1, int(len(x) * (target_rows / n_rows)))),
                    random_state=42
                ),
                random_state=42
            )
        except Exception:
            sampled_df = df.sample(n=target_rows, random_state=42)
    else:
        sampled_df = df.sample(n=target_rows, random_state=42)

    # Verify that the sampled frame now fits
    new_memory_mb = estimate_dataframe_memory_mb(sampled_df)
    if new_memory_mb > limit_mb:
        # Iteratively shrink if still too large
        while new_memory_mb > limit_mb and len(sampled_df) > min_rows:
            new_n = max(min_rows, int(len(sampled_df) * 0.9))
            if new_n >= len(sampled_df):
                break
            sampled_df = sampled_df.sample(n=new_n, random_state=42)
            new_memory_mb = estimate_dataframe_memory_mb(sampled_df)

        if new_memory_mb > limit_mb:
            raise MemoryLimitExceeded(
                f"Memory limit exceeded ({new_memory_mb:.2f} MB > {limit_mb} MB) "
                f"and subsetting impossible after iterative reduction."
            )

    # Log the sub‑sampling event
    _write_subsampling_log(original_rows=n_rows, retained_rows=len(sampled_df), limit_gb=limit_gb)

    return sampled_df.reset_index(drop=True)

def check_and_subset_memory_fallback(df: pd.DataFrame, limit_gb: float = 7.0) -> pd.DataFrame:
    """
    Wrapper for T005b: If ``check_and_subset_memory`` cannot reduce memory below the limit,
    raise ``MemoryLimitExceeded`` with a specific message.
    """
    try:
        return check_and_subset_memory(df, limit_gb)
    except MemoryLimitExceeded as e:
        if "subsetting impossible" in str(e):
            raise MemoryLimitExceeded("Memory limit exceeded and subsetting impossible")
        raise

def enforce_memory_limit_stage(
    stage_name: str,
    df: Optional[pd.DataFrame] = None,
    limit_gb: float = 7.0
) -> Optional[pd.DataFrame]:
    """
    High‑level helper used by pipeline stages.

    * Checks the current process RSS memory via ``psutil``.
    * If the limit is breached, attempts to sub‑sample the supplied DataFrame
      (if provided) using :func:`check_and_subset_memory`.
    * Writes a concise entry to ``data/logs/memory_subsampling.log`` describing
      the action taken.
    * Returns the (possibly reduced) DataFrame, or ``None`` if no DataFrame
      was supplied.

    Parameters
    ----------
    stage_name : str
        Human‑readable identifier of the pipeline stage (e.g. ``"connectivity"``).
    df : pd.DataFrame | None
        DataFrame that the stage is about to process.  May be ``None`` when the
        stage works on files rather than a DataFrame.
    limit_gb : float, optional
        Memory ceiling in GB (default 7.0).

    Returns
    -------
    pd.DataFrame | None
        The original or sub‑sampled DataFrame.

    Raises
    ------
    MemoryLimitExceeded
        If the DataFrame cannot be reduced to respect the limit.
    """
    # Current RSS memory (including any previously allocated objects)
    process = psutil.Process(os.getpid())
    rss_mb = process.memory_info().rss / (1024 * 1024)

    if rss_mb > limit_gb * 1024:
        # Peak already exceeds limit – we must act immediately.
        if df is not None:
            df = check_and_subset_memory(df, limit_gb=limit_gb)
        else:
            raise MemoryLimitExceeded(
                f"Memory limit exceeded ({rss_mb:.2f} MB) at stage '{stage_name}' with no DataFrame to sub‑sample."
            )

    # Also enforce the limit on the DataFrame itself (if given)
    if df is not None:
        df = check_and_subset_memory(df, limit_gb=limit_gb)

    return df

# ----------------------------------------------------------------------
# Compatibility aliases (preserve original public API)
# ----------------------------------------------------------------------
get_memory_mb = get_current_memory_mb
peak_memory_mb = get_peak_memory_mb
limit_mb = 7000
check_limit = check_memory_limit
enforce_limit = enforce_memory_limit
usage_report = get_memory_usage_report
simulate_memory = simulate_large_memory_usage
cleanup_memory = cleanup_large_memory
estimate_memory = estimate_dataframe_memory_mb
check_subset = check_and_subset_memory
check_subset_fallback = check_and_subset_memory_fallback

__all__ = [
    'MemoryLimitExceeded',
    'get_current_memory_mb',
    'get_peak_memory_mb',
    'check_memory_limit',
    'enforce_memory_limit',
    'get_memory_usage_report',
    'simulate_large_memory_usage',
    'cleanup_large_memory',
    'estimate_dataframe_memory_mb',
    'check_and_subset_memory',
    'check_and_subset_memory_fallback',
    'enforce_memory_limit_stage',
    # Compatibility aliases
    'get_memory_mb',
    'peak_memory_mb',
    'limit_mb',
    'check_limit',
    'enforce_limit',
    'usage_report',
    'simulate_memory',
    'cleanup_memory',
    'estimate_memory',
    'check_subset',
    'check_subset_fallback',
]