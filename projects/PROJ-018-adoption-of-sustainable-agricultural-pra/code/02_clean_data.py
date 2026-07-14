"""Data cleaning pipeline for the sustainable‑agriculture survey.

This module orchestrates the end‑to‑end cleaning steps required by
User Story 1.  In addition to the original cleaning logic it now implements
the **power‑analysis check** (Task T015).  The check calculates the ratio
``effective_N_events / num_predictors`` and records a shortfall flag in the
reproducibility log when the ratio falls below the recommended threshold of 10.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List

import pandas as pd

# --------------------------------------------------------------------------- #
# Configuration & logging utilities
# --------------------------------------------------------------------------- #
# Absolute imports are required because the scripts are executed as
# ``python code/02_clean_data.py`` (i.e. not as a package).
from config import get_config, set_random_seed
from logging_config import log_operation, update_log_section

# --------------------------------------------------------------------------- #
# Helper / decorator definitions (the decorators come from ``log_operation``)
# --------------------------------------------------------------------------- #

@log_operation("load_config")
def load_config() -> dict:
    """Return the full configuration dictionary."""
    cfg = get_config()
    # ``get_config`` may return either a Config object or a plain dict.
    # Normalise to a dict for downstream code.
    return cfg if isinstance(cfg, dict) else cfg.__dict__

@log_operation("load_raw_data")
def load_raw_data(cfg: dict) -> pd.DataFrame:
    """Read the raw CSV supplied by the upstream download step."""
    raw_dir = Path(cfg.get("raw_data_path", "data/raw"))
    raw_file = raw_dir / cfg.get("raw_data_filename", "survey_data.csv")
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file}")
    df = pd.read_csv(raw_file)
    return df

# --------------------------------------------------------------------------- #
# Validation utilities
# --------------------------------------------------------------------------- #

REQUIRED_COLUMNS = [
    "age",
    "education",
    "farm_size",
    "credit",
    "adoption",              # raw adoption indicator (may be multi‑item)
    "engagement_membership",
    "engagement_extension",
    "engagement_collective_action",
    "engagement_knowledge_exchange",
]

@log_operation("validate_variables")
def validate_variables(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Ensure required columns exist; log any gaps."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        update_log_section(
            "variable_validation",
            {"missing_columns": missing, "status": "incomplete"},
            log_path=cfg.get("modeling_log_path", "modeling_log.yaml"),
        )
    else:
        update_log_section(
            "variable_validation",
            {"missing_columns": [], "status": "complete"},
            log_path=cfg.get("modeling_log_path", "modeling_log.yaml"),
        )
    # Return the original frame – downstream steps will decide how to handle gaps.
    return df

# --------------------------------------------------------------------------- #
# Missingness handling
# --------------------------------------------------------------------------- #

@log_operation("calculate_missingness")
def calculate_missingness(df: pd.DataFrame) -> pd.Series:
    """Return a Series with the percentage of missing values per column."""
    return df.isna().mean() * 100

@log_operation("handle_missing_values")
def handle_missing_values(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """
    Drop rows with >30 % missing values.
    Impute numeric columns with the median and categorical columns with the mode.
    """
    row_missing_pct = df.isna().mean(axis=1) * 100
    df = df.loc[row_missing_pct <= 30].copy()

    for col in df.columns:
        if df[col].dtype.kind in "biufc":  # numeric types
            median = df[col].median()
            df[col].fillna(median, inplace=True)
        else:
            mode = df[col].mode()
            if not mode.empty:
                df[col].fillna(mode.iloc[0], inplace=True)
            else:
                df[col].fillna("unknown", inplace=True)
    return df

# --------------------------------------------------------------------------- #
# Normalisation of categorical codes
# --------------------------------------------------------------------------- #

@log_operation("normalize_categorical_codes")
def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise categorical string values (e.g., lower‑casing, stripping)."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.lower()
    return df

# --------------------------------------------------------------------------- #
# Power‑analysis check (Task T015)
# --------------------------------------------------------------------------- #

@log_operation("calculate_power_analysis")
def calculate_power_analysis(df: pd.DataFrame, cfg: dict) -> None:
    """
    Compute ``effective_N_events / num_predictors`` and record a shortfall
    flag when the ratio is < 10.

    * ``effective_N_events`` – count of positive outcomes in the binary
      adoption indicator ``adoption_binary`` if it exists; otherwise a
      conservative estimate of 10 % of the total sample size.
    * ``num_predictors`` – number of columns that will be used as predictors
      in downstream modelling (all columns except the outcome and any ID‑type
      columns).
    """
    # Determine the outcome column – the pipeline creates ``adoption_binary`` later,
    # but it may already be present if a previous run generated it.
    outcome_col = "adoption_binary"
    if outcome_col in df.columns:
        effective_N_events = int(df[outcome_col].sum())
    else:
        # Fallback: assume at least 10 % of the rows represent events.
        effective_N_events = max(1, int(0.10 * len(df)))

    # Predictors are all columns except the outcome and any obvious identifiers.
    exclude = {outcome_col, "respondent_id", "household_id"}
    predictor_cols = [c for c in df.columns if c not in exclude]
    num_predictors = len(predictor_cols) if predictor_cols else 1

    ratio = effective_N_events / num_predictors if num_predictors else 0.0
    shortfall = ratio < 10

    log_path = cfg.get("modeling_log_path", "modeling_log.yaml")
    update_log_section(
        "power_analysis",
        {"shortfall": shortfall, "ratio": ratio, "effective_N_events": effective_N_events, "num_predictors": num_predictors},
        log_path=log_path,
    )

# --------------------------------------------------------------------------- #
# Export cleaned data
# --------------------------------------------------------------------------- #

@log_operation("export_cleaned_data")
def export_cleaned_data(df: pd.DataFrame, cfg: dict) -> None:
    """Write the cleaned DataFrame to the processed data directory."""
    processed_dir = Path(cfg.get("processed_data_path", "data/processed"))
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / cfg.get("cleaned_data_filename", "cleaned_data.csv")
    df.to_csv(out_path, index=False)

# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #

@log_operation("data_cleaning_pipeline")
def data_cleaning_pipeline(cfg: dict) -> pd.DataFrame:
    """Run the full cleaning pipeline and return the cleaned DataFrame."""
    df = load_raw_data(cfg)
    df = validate_variables(df, cfg)
    missingness = calculate_missingness(df)
    update_log_section(
        "missingness_report",
        missingness.round(2).to_dict(),
        log_path=cfg.get("modeling_log_path", "modeling_log.yaml"),
    )
    df = handle_missing_values(df, cfg)
    df = normalize_categorical_codes(df)
    calculate_power_analysis(df, cfg)   # <-- Task T015
    export_cleaned_data(df, cfg)
    return df

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean raw survey data.")
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for any stochastic steps (default: 42).",
    )
    args = parser.parse_args(argv)

    # Ensure reproducibility for any downstream random imputation (if ever used).
    set_random_seed(args.seed)

    cfg = load_config()
    try:
        data_cleaning_pipeline(cfg)
    except Exception as exc:
        # Log the exception and exit with a non‑zero status.
        update_log_section(
            "pipeline_error",
            {"error": str(exc)},
            log_path=cfg.get("modeling_log_path", "modeling_log.yaml"),
        )
        print(f"Data cleaning failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())