"""
data.validate_raw
-----------------
Validation module for raw data before imputation.
Implements Task T013a: Sample Size Enforcement and Pre-Imputation Variable Check.

This script checks that the raw dataset contains all required variables:
    - avatar_condition
    - pre_self_esteem
    - post_self_esteem
    - comparison_tendency

It writes a JSON artifact at `data/processed/pre_imputation_validation.json`
with the following schema:
    {
        "status": "pass" | "fail",
        "missing_vars": [],
        "timestamp": "ISO8601"
    }

If any required variables are missing, the script:
    1. Writes the artifact with status "fail" and lists the missing variables.
    2. Updates `state/data_path_decision.yaml` to force the synthetic data
       generation path (decision: synthetic, reason: missing variables).
    3. Raises a RuntimeError to halt the real‑data pipeline.

The main entry point `run_validation()` is imported by `code/main.py` as
`run_raw_validation`.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import yaml

from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import DataFetchError

# ----------------------------------------------------------------------
# Configuration & Logging
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# Required variable names as defined in the project specification
REQUIRED_VARS = [
    "avatar_condition",
    "pre_self_esteem",
    "post_self_esteem",
    "comparison_tendency",
]


def _load_raw_dataframe() -> Path:
    """
    Resolve the path to the raw dataset CSV.

    The configuration may provide an explicit path via `raw_data_path`.
    If not set, we fall back to the conventional location
    `data/raw/dataset.csv`.
    """
    config = get_config()
    # `raw_data_path` is used elsewhere (e.g., preprocess) – honour it if present
    raw_path = getattr(config, "raw_data_path", None)
    if raw_path:
        raw_path = Path(raw_path)
    else:
        # Default location used throughout the code base
        raw_path = config.PROJECT_ROOT / "data" / "raw" / "dataset.csv"

    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found at expected location: {raw_path}")

    return raw_path


def _check_required_columns(csv_path: Path) -> list:
    """
    Inspect the CSV header and return a list of missing required columns.
    """
    import pandas as pd

    try:
        # Read only the header to avoid loading the whole file into memory
        df_head = pd.read_csv(csv_path, nrows=0)
    except Exception as e:
        raise DataFetchError(f"Failed to read raw CSV header: {e}")

    present = set(df_head.columns.astype(str).str.strip())
    missing = [var for var in REQUIRED_VARS if var not in present]
    return missing


def _write_validation_artifact(status: str, missing_vars: list) -> Path:
    """
    Write the JSON validation artifact.

    Parameters
    ----------
    status : str
        Either "pass" or "fail".
    missing_vars : list
        List of variable names that were not found.

    Returns
    -------
    Path
        Path to the written JSON file.
    """
    config = get_config()
    out_path = config.PROCESSED_DIR / "pre_imputation_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "status": status,
        "missing_vars": missing_vars,
        "timestamp": datetime.utcnow().isoformat(),
    }

    with open(out_path, "w") as f:
        json.dump(artifact, f, indent=2)

    logger.info(f"Pre‑imputation validation artifact written to {out_path}")
    return out_path


def _write_decision_file(decision: str, reason: str, source: str = None) -> Path:
    """
    Update `state/data_path_decision.yaml` with the supplied decision.

    Parameters
    ----------
    decision : str
        "real" or "synthetic".
    reason : str
        Human‑readable explanation for the decision.
    source : str, optional
        Identifier of the dataset source (e.g., HF dataset ID). May be None.

    Returns
    -------
    Path
        Path to the written YAML file.
    """
    config = get_config()
    state_path = config.PROJECT_ROOT / "state" / "data_path_decision.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    decision_dict = {
        "decision": decision,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
    }

    with open(state_path, "w") as f:
        yaml.safe_dump(decision_dict, f)

    logger.info(f"Data path decision updated: {decision_dict}")
    return state_path


def run_validation() -> dict:
    """
    Main validation routine called from `code/main.py`.

    Returns
    -------
    dict
        Summary of the validation outcome.
    """
    log_execution_start(logger, "pre_imputation_validation")

    try:
        raw_csv = _load_raw_dataframe()
        missing = _check_required_columns(raw_csv)

        if not missing:
            # All required variables are present
            _write_validation_artifact(status="pass", missing_vars=[])
            log_execution_end(logger, "pre_imputation_validation")
            return {"status": "pass", "missing_vars": []}

        # Missing variables – trigger synthetic fallback
        logger.warning(
            f"Missing required variables in raw data: {missing}. "
            "Falling back to synthetic data generation."
        )

        # Write the failure artifact
        _write_validation_artifact(status="fail", missing_vars=missing)

        # Record the decision so downstream tasks know to use synthetic data
        _write_decision_file(
            decision="synthetic",
            reason=f"Missing required variables: {', '.join(missing)}",
            source=None,
        )

        # Raising an exception aborts the current pipeline run.
        # The higher‑level `download` step (T009b) will have already
        # generated the synthetic seed; this stop prevents any further
        # processing of the incomplete real dataset.
        raise RuntimeError(
            "Pre‑imputation validation failed – required variables missing. "
            "Synthetic data path selected."
        )

    except Exception as exc:
        # Ensure any unexpected error is logged and re‑raised so the
        # pipeline fails loudly (no silent fallback).
        logger.error(f"Pre‑imputation validation encountered an error: {exc}", exc_info=True)
        raise

# ----------------------------------------------------------------------
# CLI entry point (useful for manual debugging)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        result = run_validation()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Validation failed: {e}")
        exit(1)