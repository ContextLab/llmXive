"""
Aggregate per‑configuration statistics into a contract‑compliant CSV.

This script reads the Monte‑Carlo sweep results (``mc_results.csv``) and the
statistical threshold estimates (``threshold_statistical.json``), computes the
aggregate metrics required by the ``AggregatedThreshold`` contract, writes the
CSV file ``threshold_sweep_results.csv`` (one row per (N, k, pattern_type)
configuration), and finally runs the Pydantic validator
``code/analysis/validate_aggregated.py`` which logs PASS/FAIL for each row to
``data/logs/aggregation_validation.txt``.

The script is intended to be invoked directly:

```bash
python code/analysis/aggregate_thresholds.py
```

It exits with the return code of the validator (0 = all rows PASS).
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
from utils.config import get_project_paths

def _setup_logger() -> logging.Logger:
    """Configure a simple console + file logger."""
    logger = logging.getLogger("aggregate_thresholds")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

# ----------------------------------------------------------------------
# Core aggregation logic
# ----------------------------------------------------------------------
def _load_mc_results(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load ``mc_results.csv`` and verify required columns."""
    if not path.is_file():
        logger.error(f"Monte‑Carlo results file not found: {path}")
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    required = {"N", "k", "pattern_type", "outlier_flag", "deviation"}
    missing = required.difference(df.columns)
    if missing:
        logger.error(
            f"mc_results.csv is missing required columns: {sorted(missing)}"
        )
        raise ValueError(f"Missing columns {missing}")

    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def _load_statistical_thresholds(path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load ``threshold_statistical.json`` – expected to be a list of dicts."""
    if not path.is_file():
        logger.error(f"Statistical thresholds file not found: {path}")
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # The JSON is expected to be a list of records, each containing at least
    # N, k, pattern_type, theta_c_estimate and theta_c_confidence (a dict with
    # lower/upper).  Convert to a DataFrame for easy merging.
    df = pd.DataFrame(data)

    required = {"N", "k", "pattern_type", "theta_c_estimate", "theta_c_confidence"}
    missing = required.difference(df.columns)
    if missing:
        logger.error(
            f"threshold_statistical.json is missing required keys: {sorted(missing)}"
        )
        raise ValueError(f"Missing keys {missing}")

    logger.info(f"Loaded statistical thresholds for {len(df)} groups from {path}")
    return df

def _aggregate_mc_results(df_mc: pd.DataFrame) -> pd.DataFrame:
    """
    Compute aggregate metrics per (N, k, pattern_type).

    Returns a DataFrame with columns:
        N, k, pattern_type,
        total_runs, outlier_count, outlier_probability,
        mean_deviation, std_deviation
    """
    agg = (
        df_mc.groupby(["N", "k", "pattern_type"])
        .agg(
            total_runs=("outlier_flag", "size"),
            outlier_count=("outlier_flag", "sum"),
            mean_deviation=("deviation", "mean"),
            std_deviation=("deviation", "std"),
        )
        .reset_index()
    )
    # Probability of outlier emergence
    agg["outlier_probability"] = agg["outlier_count"] / agg["total_runs"]
    return agg

def _merge_with_thresholds(
    agg_mc: pd.DataFrame, df_thresh: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame:
    """
    Merge Monte‑Carlo aggregates with the statistical threshold estimates.

    The ``theta_c_confidence`` field is a dict; we split it into lower/upper
    columns so that the CSV matches the contract schema.
    """
    merged = pd.merge(
        agg_mc,
        df_thresh,
        on=["N", "k", "pattern_type"],
        how="left",
        suffixes=("", "_stat"),
    )

    # Expand the confidence interval dict into two separate columns.
    if "theta_c_confidence" in merged.columns:
        def _extract(conf, key):
            if isinstance(conf, dict):
                return conf.get(key)
            return None

        merged["theta_c_confidence_lower"] = merged["theta_c_confidence"].apply(
            lambda c: _extract(c, "lower")
        )
        merged["theta_c_confidence_upper"] = merged["theta_c_confidence"].apply(
            lambda c: _extract(c, "upper")
        )
        merged = merged.drop(columns=["theta_c_confidence"])

    # Re‑order columns for readability / contract compliance.
    column_order = [
        "N",
        "k",
        "pattern_type",
        "total_runs",
        "outlier_count",
        "outlier_probability",
        "mean_deviation",
        "std_deviation",
        "theta_c_estimate",
        "theta_c_confidence_lower",
        "theta_c_confidence_upper",
    ]
    merged = merged[column_order]
    logger.info(
        f"Merged aggregates with thresholds – resulting rows: {len(merged)}"
    )
    return merged

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    logger = _setup_logger()
    paths = get_project_paths()

    mc_path = paths["processed"] / "mc_results.csv"
    thresh_path = paths["processed"] / "threshold_statistical.json"
    output_path = paths["processed"] / "threshold_sweep_results.csv"

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    try:
        df_mc = _load_mc_results(mc_path, logger)
        df_thresh = _load_statistical_thresholds(thresh_path, logger)
    except Exception as exc:
        logger.exception(f"Failed to load input data: {exc}")
        return 1

    # ------------------------------------------------------------------
    # Aggregate Monte‑Carlo results
    # ------------------------------------------------------------------
    agg_mc = _aggregate_mc_results(df_mc)

    # ------------------------------------------------------------------
    # Merge with statistical thresholds
    # ------------------------------------------------------------------
    merged = _merge_with_thresholds(agg_mc, df_thresh, logger)

    # ------------------------------------------------------------------
    # Write CSV output
    # ------------------------------------------------------------------
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(output_path, index=False)
        logger.info(f"Aggregated CSV written to {output_path}")
    except Exception as exc:
        logger.exception(f"Failed to write CSV: {exc}")
        return 1

    # ------------------------------------------------------------------
    # Run the Pydantic validator
    # ------------------------------------------------------------------
    try:
        # The validator script lives at ``code/analysis/validate_aggregated.py``.
        # It defines a ``main`` function that returns an exit code.
        from analysis.validate_aggregated import main as validator_main
    except Exception as exc:
        logger.exception(f"Could not import validator: {exc}")
        return 1

    logger.info("Running Pydantic validator on the aggregated CSV …")
    try:
        ret = validator_main()
        if ret == 0:
            logger.info("All rows passed validation.")
        else:
            logger.warning(
                f"Validator reported non‑zero exit code ({ret}). See "
                f"{paths['data_logs'] / 'aggregation_validation.txt'}"
            )
        return ret
    except Exception as exc:
        logger.exception(f"Validator raised an exception: {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())