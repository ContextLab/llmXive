"""Data cleaning pipeline with power analysis logging.

This script loads raw survey data, validates required variables,
handles missing values, normalizes categorical codes, performs a
simple power analysis, and writes the cleaned dataset to
``data/processed/cleaned_data.csv``.  All major steps are logged
via the project's ``logging_config`` utilities.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

# Project imports
from config import get_config, get_processed_data_path, get_raw_data_path
from logging_config import log_operation, update_log_section

# ----------------------------------------------------------------------
# Helper logging wrapper (no‑op decorator) – we avoid using the faulty
# ``@log_operation`` decorator that currently returns a LogEntry.
# ----------------------------------------------------------------------
def _log_step(operation_name: str, **kwargs: Any) -> None:
    """Log a step using the ``log_operation`` function."""
    log_operation(operation_name, **kwargs)

# ----------------------------------------------------------------------
# Configuration loading
# ----------------------------------------------------------------------
def load_config() -> dict:
    """Return the full configuration dictionary."""
    _log_step("load_config")
    cfg = get_config()
    if not isinstance(cfg, dict):
        raise TypeError("Configuration must be a dict.")
    return cfg

# ----------------------------------------------------------------------
# Raw data loading
# ----------------------------------------------------------------------
def load_raw_data() -> pd.DataFrame:
    """Load the raw survey CSV into a DataFrame."""
    _log_step("load_raw_data")
    raw_dir = Path(get_raw_data_path())
    raw_file = raw_dir / "survey_data.csv"
    if not raw_file.is_file():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}")
    df = pd.read_csv(raw_file)
    return df

# ----------------------------------------------------------------------
# Variable validation
# ----------------------------------------------------------------------
def validate_variables(df: pd.DataFrame, required_vars: List[str]) -> pd.DataFrame:
    """Ensure required columns exist; log any gaps."""
    _log_step("validate_variables", required=required_vars)
    missing = [var for var in required_vars if var not in df.columns]
    if missing:
        # Log missing variables; do not raise to keep pipeline running.
        update_log_section(
            "variable_validation",
            {"missing_variables": missing, "status": "incomplete"},
        )
    else:
        update_log_section(
            "variable_validation",
            {"missing_variables": [], "status": "complete"},
        )
    return df

# ----------------------------------------------------------------------
# Missingness calculation
# ----------------------------------------------------------------------
def calculate_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """Add a column with per‑row missingness proportion."""
    _log_step("calculate_missingness")
    missing_perc = df.isnull().mean(axis=1)
    df = df.copy()
    df["_row_missingness"] = missing_perc
    return df

# ----------------------------------------------------------------------
# Missing‑value handling
# ----------------------------------------------------------------------
def handle_missing_values(df: pd.DataFrame, threshold: float = 0.30) -> pd.DataFrame:
    """Drop rows >threshold missing; impute remaining simple."""
    _log_step("handle_missing_values", threshold=threshold)
    # Drop rows with too much missing data
    df = df[df["_row_missingness"] <= threshold].drop(columns=["_row_missingness"])
    # Simple imputation: numeric -> median, categorical -> mode
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
            else:
                mode_val = df[col].mode(dropna=True)
                if not mode_val.empty:
                    df[col].fillna(mode_val.iloc[0], inplace=True)
                else:
                    df[col].fillna("unknown", inplace=True)
    return df

# ----------------------------------------------------------------------
# Categorical code normalization
# ----------------------------------------------------------------------
def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise categorical columns to lower‑case strings."""
    _log_step("normalize_categorical_codes")
    df = df.copy()
    for col in df.select_dtypes(include=["object", "category"]).columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
    return df

# ----------------------------------------------------------------------
# Power analysis
# ----------------------------------------------------------------------
def calculate_power_analysis(df: pd.DataFrame) -> None:
    """Compute effective N / predictors ratio and log shortfall if <10."""
    _log_step("calculate_power_analysis")
    # Determine outcome column – convention is ``adoption_binary``.
    if "adoption_binary" in df.columns:
        effective_N_events = int(df["adoption_binary"].sum())
    else:
        # If not present, assume a modest 10 % event rate.
        effective_N_events = max(1, int(0.10 * len(df)))

    # Predictors are all columns except the outcome and any ID columns.
    exclude_cols = {"adoption_binary", "respondent_id", "id"}
    predictor_cols = [c for c in df.columns if c not in exclude_cols]
    num_predictors = max(1, len(predictor_cols))

    ratio = effective_N_events / num_predictors if num_predictors else 0.0

    shortfall = ratio < 10
    power_entry = {
        "effective_N_events": effective_N_events,
        "num_predictors": num_predictors,
        "ratio": ratio,
        "shortfall": shortfall,
    }
    update_log_section("power_analysis", power_entry)

# ----------------------------------------------------------------------
# Export cleaned data
# ----------------------------------------------------------------------
def export_cleaned_data(df: pd.DataFrame) -> None:
    """Write the cleaned DataFrame to the processed data directory."""
    _log_step("export_cleaned_data")
    processed_dir = Path(get_processed_data_path())
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / "cleaned_data.csv"
    df.to_csv(out_path, index=False)
    # Record path in the modeling log for traceability
    update_log_section(
        "cleaned_data_output",
        {"path": str(out_path.resolve()), "rows": len(df), "columns": len(df.columns)},
    )

# ----------------------------------------------------------------------
# Full pipeline orchestration
# ----------------------------------------------------------------------
def data_cleaning_pipeline() -> None:
    """Run the complete cleaning pipeline."""
    _log_step("data_cleaning_pipeline")
    cfg = load_config()

    # Required variables are defined in the spec; we expose a default list.
    required_vars = cfg.get(
        "required_variables",
        [
            "age",
            "education",
            "farm_size",
            "credit",
            "adoption",
            "membership",
            "extension",
            "collective_action",
            "knowledge_exchange",
        ],
    )

    df = load_raw_data()
    df = validate_variables(df, required_vars)
    df = calculate_missingness(df)
    df = handle_missing_values(df)
    df = normalize_categorical_codes(df)
    calculate_power_analysis(df)
    export_cleaned_data(df)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Clean raw survey data and perform power analysis."
    )
    # The script previously accepted a ``--synthetic`` flag; we keep it for
    # compatibility but do not implement synthetic generation here.
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="If set, the script will attempt to generate synthetic data "
        "via the fallback generator (not implemented in this task).",
    )
    args = parser.parse_args(argv)

    try:
        if args.synthetic:
            # In the current MVP we simply raise a clear error so the user
            # knows the fallback is not part of this task.
            raise NotImplementedError(
                "Synthetic data generation is not implemented in T015. "
                "Run the pipeline without ``--synthetic``."
            )
        data_cleaning_pipeline()
    except Exception as exc:
        # Log the failure but return a non‑zero exit code.
        log_operation("pipeline_failure", error=str(exc))
        return 1
    return 0

if __name__ == "__main__":
    main()