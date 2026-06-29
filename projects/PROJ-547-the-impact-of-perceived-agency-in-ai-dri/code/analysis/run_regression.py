"""
run_regression.py
-----------------
This module runs the regression analysis pipeline while profiling memory usage.
It ensures that peak RAM consumption stays below the 6 GB threshold defined by
functional requirement FR‑007.

The script can be executed directly:

    python code/analysis/run_regression.py --input data/processed/merged_data.csv \\
                                          --output data/processed/regression_results.csv

The memory profiling results are written to
`data/processed/memory_profile.json` (JSON with a single key ``peak_ram_mb``).
"""
from __future__ import annotations

import argparse
import json
import threading
import time
from pathlib import Path
from typing import Tuple

import pandas as pd
import psutil
import statsmodels.api as sm

from analysis.select_regression import select_regression
from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError, log_and_exit

# ----------------------------------------------------------------------
# Memory profiling utilities
# ----------------------------------------------------------------------
class MemoryProfiler(threading.Thread):
    """Background thread that records the process's RSS memory usage."""

    def __init__(self, interval: float = 0.1):
        super().__init__(daemon=True)
        self.interval = interval
        self._peak = 0
        self._running = threading.Event()
        self._running.set()
        self.process = psutil.Process()

    def run(self) -> None:
        while self._running.is_set():
            try:
                rss = self.process.memory_info().rss
                if rss > self._peak:
                    self._peak = rss
            finally:
                time.sleep(self.interval)

    def stop(self) -> None:
        self._running.clear()

    @property
    def peak(self) -> int:
        """Return the highest observed RSS memory in bytes."""
        return self._peak

# ----------------------------------------------------------------------
# Core regression routine
# ----------------------------------------------------------------------
def run_regression(
    merged_path: Path,
    results_path: Path,
    memory_profile_path: Path,
    ram_limit_bytes: int = 6 * 1024**3,
) -> None:
    """
    Execute the regression pipeline.

    Parameters
    ----------
    merged_path: Path
        Path to the merged dataset CSV produced by ``merge_datasets``.
    results_path: Path
        Destination CSV where regression coefficients and statistics are saved.
    memory_profile_path: Path
        Destination JSON file that records the peak RAM usage (in MB).
    ram_limit_bytes: int, optional
        Upper bound for RAM consumption. Default is 6 GB.
    """
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Start memory profiling
    # ------------------------------------------------------------------
    profiler = MemoryProfiler()
    profiler.start()
    logger.info("Memory profiling started.")

    try:
        # ----------------------------------------------------------------
        # Load merged data
        # ----------------------------------------------------------------
        logger.info("Loading merged dataset.", extra={"path": str(merged_path)})
        data = pd.read_csv(merged_path)

        # ----------------------------------------------------------------
        # Determine outcome type and select appropriate regression model
        # ----------------------------------------------------------------
        logger.info("Selecting regression model.")
        model, X, y = select_regression(data)

        # ----------------------------------------------------------------
        # Fit the model
        # ----------------------------------------------------------------
        logger.info("Fitting regression model.")
        results = model.fit()

        # ----------------------------------------------------------------
        # Persist results
        # ----------------------------------------------------------------
        logger.info("Saving regression results.", extra={"path": str(results_path)})
        # Convert results summary to a DataFrame for CSV export
        summary_df = pd.read_html(results.summary().tables[1])[0]
        summary_df.to_csv(results_path, index=False)

    except Exception as exc:
        # Any unexpected error should be logged and cause a clean exit
        log_and_exit(exc, logger)

    finally:
        # ------------------------------------------------------------------
        # Stop profiling and write the memory report
        # ------------------------------------------------------------------
        profiler.stop()
        peak_bytes = profiler.peak
        peak_mb = round(peak_bytes / (1024**2), 2)
        logger.info(
            "Memory profiling stopped.",
            extra={"peak_ram_mb": peak_mb},
        )

        # Write JSON report
        memory_profile_path.parent.mkdir(parents=True, exist_ok=True)
        with memory_profile_path.open("w", encoding="utf-8") as fp:
            json.dump({"peak_ram_mb": peak_mb}, fp, indent=2)

        # Enforce RAM limit
        if peak_bytes > ram_limit_bytes:
            err_msg = (
                f"Peak RAM usage {peak_mb} MB exceeds the allowed limit of "
                f"{ram_limit_bytes / (1024**3)} GB."
            )
            logger.error(err_msg)
            raise PipelineError(err_msg)
