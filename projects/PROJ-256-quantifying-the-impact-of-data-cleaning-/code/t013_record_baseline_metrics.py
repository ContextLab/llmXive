"""
T013 – Record baseline metrics

This script loads raw datasets, runs the baseline statistical analysis and
writes the results to ``data/processed/baseline_metrics.json`` with at
least three decimal places of precision.
"""

import json
import logging
import sys
from pathlib import Path

from utils import setup_logging, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis

logger = setup_logging("INFO")

def main() -> int:
    """
    Entrypoint for the baseline‑recording task.

    Returns:
        int: exit code (0 for success, non‑zero for failure)
    """
    try:
        # Ensure reproducibility
        cfg = get_config()
        seed = cfg.get("RANDOM_SEED", 42)
        pin_random_seed(int(seed))

        raw_dir = cfg.get("RAW_DATA_PATH", "data/raw")
        processed_dir = cfg.get("PROCESSED_DATA_PATH", "data/processed")
        output_path = Path(processed_dir) / "baseline_metrics.json"

        logger.info(f"Running baseline analysis on raw data in {raw_dir}")
        metrics = run_baseline_analysis(str(raw_dir), str(output_path))

        # Validate that we have numeric p‑values and CI bounds
        for ds_name, ds_metrics in metrics.items():
            if isinstance(ds_metrics, dict):
                t_test = ds_metrics.get("t_test", {})
                p = t_test.get("p_value")
                ci = t_test.get("ci", [])
                if not (isinstance(p, float) and 0.0 < p < 1.0):
                    logger.warning(f"Dataset {ds_name} produced an unexpected p‑value: {p}")
                if ci and (not all(isinstance(v, float) and np.isfinite(v) for v in ci)):
                    logger.warning(f"Dataset {ds_name} produced non‑finite CI values: {ci}")

        logger.info(f"Baseline metrics written to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to record baseline metrics: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())