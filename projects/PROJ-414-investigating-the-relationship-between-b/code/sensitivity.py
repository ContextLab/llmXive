"""Sensitivity analysis for sliding‑window parameters.

This script re‑runs the descriptor computation (connectivity stage) for
each combination of window size and step size defined in ``config`` and
aggregates simple statistics of the resulting vertex‑block connectivity
descriptors. If the conditional association stage (``analysis``) produced
regression results, the standard deviation of the correlation coefficients
across PCs is also reported; otherwise a placeholder string
``not_computable_no_skill_proxy`` is written (SC‑002).

The output ``results/sensitivity_summary.csv`` contains exactly six rows,
one per (window, step) combination, with the following columns:

  - window_seconds: float
  - step_seconds:   float
  - descriptor_mean: float
  - descriptor_sd:   float
  - descriptor_range: float  (max − min)
  - correlation_sd:  float | "not_computable_no_skill_proxy"
"""
import importlib
import json
import os
from pathlib import Path

import pandas as pd

import config
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_stage(module_name: str) -> int:
    """Import a stage module from ``code`` and execute its ``main``."""
    module = importlib.import_module(f"code.{module_name}")
    if not hasattr(module, "main"):
        raise AttributeError(f"Module {module_name} has no main()")
    log.info("Running stage %s", module_name)
    return module.main([])

def _collect_descriptor_stats() -> dict:
    """Load all per‑subject metric CSVs and compute summary statistics.

    Returns a dict with keys: mean, sd, min, max, range.
    """
    derived_dir = paths.data("derived")
    metric_files = sorted(derived_dir.glob("metrics_*.csv"))
    if not metric_files:
        log.warning("No metric files found for sensitivity aggregation")
        return {"mean": float("nan"), "sd": float("nan"),
                "min": float("nan"), "max": float("nan"),
                "range": float("nan")}

    dfs = [pd.read_csv(f) for f in metric_files]
    df_all = pd.concat(dfs, ignore_index=True)

    # Exclude non‑numeric identifier columns
    numeric_cols = df_all.select_dtypes(include=["number"]).columns
    # Remove possible identifier columns that are numeric (e.g. window_index)
    exclude_cols = {"window_index"}
    numeric_cols = [c for c in numeric_cols if c not in exclude_cols]

    if not numeric_cols:
        log.warning("No numeric descriptor columns found")
        return {"mean": float("nan"), "sd": float("nan"),
                "min": float("nan"), "max": float("nan"),
                "range": float("nan")}

    data = df_all[numeric_cols].to_numpy().ravel()
    mean = float(data.mean())
    sd = float(data.std(ddof=1))
    min_val = float(data.min())
    max_val = float(data.max())
    return {"mean": mean, "sd": sd, "min": min_val,
            "max": max_val, "range": max_val - min_val}

def _correlation_sd_from_analysis() -> float | str:
    """Extract the standard deviation of correlation coefficients from
    ``results/regression_results.csv`` if it exists.

    The regression results file is expected to contain a column named
    ``correlation`` (or ``r``) for each principal component. If the file
    is missing or the column is absent, the placeholder string is
    returned.
    """
    reg_path = paths.results("regression_results.csv")
    if not reg_path.is_file():
        log.info("Regression results not found – association stage likely skipped")
        return "not_computable_no_skill_proxy"

    df = pd.read_csv(reg_path)
    # Accept common column names for the correlation coefficient
    for col in ("correlation", "r", "beta"):
        if col in df.columns:
            corr_vals = df[col].astype(float).dropna()
            if len(corr_vals) == 0:
                return "not_computable_no_skill_proxy"
            return float(corr_vals.std(ddof=1))
    return "not_computable_no_skill_proxy"

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    """Run the sensitivity sweep and write ``results/sensitivity_summary.csv``."""
    # Ensure the results directory exists
    results_dir = paths.results()
    results_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    # Preserve original defaults to restore after the sweep
    orig_window = config.DEFAULT_WINDOW_SECONDS
    orig_step = config.DEFAULT_STEP_SECONDS

    try:
        for window in config.SENSITIVITY_WINDOW_SECONDS:
            for step in config.SENSITIVITY_STEP_SECONDS:
                log.info("Sensitivity run – window=%.1f s, step=%.1f s", window, step)
                # Override the global config values for this run
                config.DEFAULT_WINDOW_SECONDS = float(window)
                config.DEFAULT_STEP_SECONDS = float(step)

                # Re‑run the connectivity stage (which writes metrics_*.csv)
                ret = _run_stage("connectivity")
                if ret not in (0, None):
                    raise RuntimeError(f"connectivity stage failed with code {ret}")

                # Re‑run the optional association stage
                # (analysis will internally decide whether to run)
                _run_stage("analysis")

                # Aggregate descriptor statistics for this parameter setting
                stats = _collect_descriptor_stats()
                corr_sd = _correlation_sd_from_analysis()

                summary_rows.append({
                    "window_seconds": float(window),
                    "step_seconds": float(step),
                    "descriptor_mean": stats["mean"],
                    "descriptor_sd": stats["sd"],
                    "descriptor_range": stats["range"],
                    "correlation_sd": corr_sd,
                })
    finally:
        # Restore original configuration values
        config.DEFAULT_WINDOW_SECONDS = orig_window
        config.DEFAULT_STEP_SECONDS = orig_step

    # Write the summary CSV
    summary_path = results_dir / "sensitivity_summary.csv"
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv(summary_path, index=False)
    log.info("Sensitivity summary written to %s", summary_path)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
