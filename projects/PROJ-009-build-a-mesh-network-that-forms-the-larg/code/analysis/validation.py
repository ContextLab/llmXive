"""
Variable‑Fit verification script.

This module is invoked by ``code/analysis/aggregate.py`` after the
aggregated ``execution_runs.csv`` file has been written.  It checks that
every required predictor and outcome column is present for each run and
writes an updated ``validation_status.json`` file under ``data/raw/``.
"""

import json
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Mapping of required logical variables to the column names used in
# ``execution_runs.csv``.  If a column is missing or contains a NaN value,
# the run is marked ``excluded`` with a reason that lists the missing
# variables.
# ----------------------------------------------------------------------
REQUIRED_PREDICTORS = {
    "cpu_variance": "cpu_variance",
    "dropout_rate": "dropout_rate",
    "node_count": "node_count",
    "granularity_setting": "granularity_setting",
    "injected_latency": "injected_latency_ms",
}

REQUIRED_OUTCOMES = {
    "total_throughput": "throughput_ops",
}

def _missing_columns(row: pd.Series) -> list[str]:
    """
    Determine which required columns are missing or NaN for a given row.

    Parameters
    ----------
    row: pandas.Series
        A single run record from ``execution_runs.csv``.

    Returns
    -------
    list[str]
        Logical names of the missing variables (e.g. ``"cpu_variance"``).
    """
    missing: list[str] = []

    for logical, col in {**REQUIRED_PREDICTORS, **REQUIRED_OUTCOMES}.items():
        if col not in row or pd.isna(row[col]):
            missing.append(logical)

    return missing

def main() -> int:
    """
    Entry point for the validation step.

    Reads ``data/processed/execution_runs.csv`` and writes
    ``data/raw/validation_status.json``.  The JSON structure maps each
    ``run_id`` to a dictionary with keys ``status`` (``included`` or
    ``excluded``) and ``reason`` (human‑readable explanation).

    Returns
    -------
    int
        Exit status (0 on success, non‑zero on failure).
    """
    csv_path: Path = paths.processed("execution_runs.csv")
    if not csv_path.exists():
        log.error("Aggregated execution runs file not found: %s", csv_path)
        raise FileNotFoundError(csv_path)

    df: pd.DataFrame = pd.read_csv(csv_path, dtype=str)

    validation_status: dict[str, dict[str, str]] = {}

    for _, row in df.iterrows():
        run_id = str(row.get("run_id"))
        missing = _missing_columns(row)

        if missing:
            status = "excluded"
            reason = f"missing columns: {', '.join(missing)}"
        else:
            status = "included"
            reason = "all required variables present"

        validation_status[run_id] = {"status": status, "reason": reason}

    out_path: Path = paths.raw("validation_status.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(validation_status, indent=2, sort_keys=True))

    log.info("Wrote validation status for %d runs to %s", len(validation_status), out_path)
    return 0
