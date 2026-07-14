"""
Main entry point for the llmXive sleep centrality analysis pipeline.

This module sets up logging, provides utilities for memory usage profiling,
measures total runtime, and verifies that the execution time stays below a
configurable target (default 4 hours) on a 2 vCPU runner as required by
SC‑002.

The ``main`` function orchestrates the full pipeline by delegating to the
``quickstart_validator`` module, which runs the end‑to‑end workflow
(download → preprocess → metrics → analysis → report).
"""

import logging
import sys
import os
import time
import resource
from pathlib import Path
from typing import Callable, Any

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger with a simple format.

    Parameters
    ----------
    level : int, optional
        Logging level for the root logger. Defaults to ``logging.INFO``.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.debug("Logging configured with level %s", logging.getLevelName(level))

# ----------------------------------------------------------------------
# Memory usage helpers
# ----------------------------------------------------------------------
def get_memory_usage_bytes() -> int:
    """
    Return the current process' memory usage in bytes.

    Uses ``resource.getrusage`` which reports memory in kilobytes on Linux
    and in bytes on macOS. The function normalises the result to bytes.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ``ru_maxrss`` is in kilobytes on Linux, bytes on macOS.
    rss = usage.ru_maxrss
    if sys.platform.startswith("linux"):
        rss *= 1024  # convert KiB -> bytes
    return int(rss)

def profile_memory_usage(func: Callable) -> Callable:
    """
    Decorator that logs memory usage before and after a function call.

    The decorator records the peak memory usage (as reported by
    ``get_memory_usage_bytes``) after the wrapped function finishes and logs
    it at INFO level.

    Parameters
    ----------
    func : Callable
        Function to be wrapped.

    Returns
    -------
    Callable
        Wrapped function with memory profiling.
    """
    def wrapper(*args, **kwargs) -> Any:
        logging.debug("Memory profiling start for %s", func.__name__)
        start_mem = get_memory_usage_bytes()
        result = func(*args, **kwargs)
        end_mem = get_memory_usage_bytes()
        peak_mem = max(start_mem, end_mem)
        logging.info(
            "Memory usage for %s: %.2f MB (peak)",
            func.__name__,
            peak_mem / (1024 * 1024),
        )
        # Enforce the 4 GB ceiling required by SC‑002
        max_allowed = 4 * 1024 * 1024 * 1024  # 4 GB in bytes
        if peak_mem > max_allowed:
            logging.warning(
                "Peak memory usage (%.2f GB) exceeds the 4 GB limit.",
                peak_mem / (1024 ** 3),
            )
        return result
    return wrapper

# ----------------------------------------------------------------------
# Runtime verification
# ----------------------------------------------------------------------
def verify_runtime_target(elapsed_seconds: float, max_seconds: float = 4 * 3600) -> bool:
    """
    Verify that the total runtime does not exceed the target.

    Logs an INFO message when the runtime is within the limit and a
    WARNING when it exceeds the limit.

    Parameters
    ----------
    elapsed_seconds : float
        Total elapsed time measured for the pipeline run.
    max_seconds : float, optional
        Maximum allowed runtime in seconds. Defaults to 4 hours.

    Returns
    -------
    bool
        ``True`` if the runtime is within the target, ``False`` otherwise.
    """
    elapsed_hours = elapsed_seconds / 3600
    max_hours = max_seconds / 3600
    if elapsed_seconds <= max_seconds:
        logging.info(
            "Pipeline completed in %.2f hours (target ≤ %.2f hours).",
            elapsed_hours,
            max_hours,
        )
        return True
    else:
        logging.warning(
            "Pipeline runtime %.2f hours exceeds the target of %.2f hours.",
            elapsed_hours,
            max_hours,
        )
        return False

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
@profile_memory_usage
def run_full_pipeline() -> None:
    """
    Execute the full analysis pipeline.

    The implementation delegates to ``quickstart_validator.main`` which
    runs all required stages (download, preprocessing, metric computation,
    statistical analysis, and report generation). Import is performed
    lazily to avoid unnecessary overhead when the module is imported but
    not executed.
    """
    logging.debug("Importing quickstart_validator for pipeline execution.")
    from quickstart_validator import main as quickstart_main

    # The quickstart validator returns an exit code; we propagate it.
    exit_code = quickstart_main()
    if exit_code != 0:
        logging.error(
            "Quickstart validator exited with non‑zero code %d.", exit_code
        )
        sys.exit(exit_code)

def main() -> int:
    """
    Entry point for ``python -m code.main`` or ``python code/main.py``.

    It sets up logging, records the start time, runs the full pipeline,
    measures elapsed time, verifies the runtime target, and returns an
    appropriate exit code.
    """
    setup_logging()
    logging.info("Starting llmXive sleep centrality pipeline.")
    start_time = time.time()

    try:
        run_full_pipeline()
    except Exception as exc:
        logging.exception("Pipeline execution failed: %s", exc)
        return 1

    end_time = time.time()
    elapsed = end_time - start_time
    logging.info("Total pipeline runtime: %.2f seconds (%.2f minutes).",
                 elapsed, elapsed / 60)

    # Verify that we stayed within the 4‑hour budget.
    verify_runtime_target(elapsed)

    logging.info("Pipeline finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())