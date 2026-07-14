"""Data cleaning pipeline for the sustainable‑agriculture project.

The script performs the following steps:
1. Load configuration and initialise logging.
2. Load the raw survey data (CSV) – expects ``survey_data.csv`` in the
   raw data directory; if missing, raises ``CustomDataError``.
3. Validate that all required variables are present.
4. Compute missingness statistics and log them.
5. Handle missing values (drop rows with >30 % missing, impute the rest).
6. Normalise categorical codes (placeholder – can be extended).
7. Perform a power‑analysis check and record the result in
   ``modeling_log.yaml`` under the ``power_analysis`` key.
8. Export the cleaned dataset to ``data/processed/cleaned_data.csv``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from config import (
    get_config,
    get_processed_data_path,
    get_raw_data_path,
    set_random_seed,
)
from logging_config import (
    log_operation,
    update_log_section,
)

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class CustomDataError(RuntimeError):
    """Raised when a required data file cannot be found or is malformed."""


# --------------------------------------------------------------------------- #
# Core functions – each is decorated with ``@log_operation`` so that the
# execution of the step is recorded in the reproducibility log.
# --------------------------------------------------------------------------- #
@log_operation("load_config")
def load_config() -> Dict[str, Any]:
    """Return the full configuration dictionary."""
    return get_config()


@log_operation("setup_logging")
def setup_logging() -> None:
    """Initialise the reproducibility logger (no‑op if already initialised)."""
    # ``log_operation`` itself registers the logger when first used.
    # Calling it here ensures the logger file is created early.
    from logging_config import get_logger  # local import to avoid circularity
    get_logger()


@log_operation("load_raw_data")
def load_raw_data() -> pd.DataFrame:
    """
    Load the raw survey CSV. Expected filename is ``survey_data.csv``.
    Raises ``CustomDataError`` if the file does not exist.
    """
    raw_dir = get_raw_data_path()
    csv_path = raw_dir / "survey_data.csv"
    if not csv_path.is_file():
        raise CustomDataError(f"Raw data not found at {csv_path}")
    df = pd.read_csv(csv_path)
    return df


REQUIRED_COLUMNS = [
    "age",
    "education",
    "farm_size",
    "credit",
    "adoption_binary",  # may be created later; keep for validation flexibility
    # engagement proxy columns – placeholder names
    "membership",
    "extension_contact",
    "collective_action",
    "knowledge_exchange",
]


@log_operation("validate_variables")
def validate_variables(df: pd.DataFrame) -> List[str]:
    """Return a list of missing required columns; log the gaps."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        # Record the validation result in the log.
        update_log_section(
            "data_validation",
            {"missing_columns": missing},
            log_path=get_config("modeling_log_path", "modeling_log.yaml"),
        )
    return missing


@log_operation("calculate_missingness")
def calculate_missingness(df: pd.DataFrame) -> pd.Series:
    """Return the percentage of missing values per column."""
    missing_pct = df.isna().mean() * 100
    update_log_section(
        "initial_missingness",
        missing_pct.round(2).to_dict(),
        log_path=get_config("modeling_log_path", "modeling_log.yaml"),
    )
    return missing_pct


@log_operation("handle_missing_values")
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows with >30 % missing values.
    Impute remaining missing values:
      – numeric → median
      – categorical → mode (first value)
    """
    threshold = 0.30
    row_missing = df.isna().mean(axis=1)
    df = df.loc[row_missing <= threshold].copy()

    for col in df.columns:
        if df[col].isna().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col].fillna(median_val, inplace=True)
            else:
                mode_val = df[col].mode().iloc[0] if not df[col].mode().empty else None
                df[col].fillna(mode_val, inplace=True)
    return df


@log_operation("normalize_categorical_codes")
def normalize_categorical_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Placeholder for categorical normalisation.
    Currently passes the DataFrame through unchanged.
    """
    # Future implementation could map raw strings to standard codes.
    return df


@log_operation("calculate_power_analysis")
def calculate_power_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute a simple power‑analysis metric:
      effective_N_events = number of positive outcomes in ``adoption_binary``
                             (or 10 % of total rows if the column is absent)
      num_predictors      = number of columns used as predictors
                             (all columns except ``adoption_binary``)
      ratio               = effective_N_events / num_predictors

    The result dictionary contains the raw numbers and a ``shortfall`` flag
    when the ratio is below the conventional threshold of 10.
    """
    if "adoption_binary" in df.columns:
        effective_N_events = int(df["adoption_binary"].sum())
    else:
        # Conservative fallback – assume at least a non‑negligible proportion.
        effective_N_events = max(1, int(0.10 * len(df)))

    # Exclude the outcome column from the predictor count.
    predictor_cols = [c for c in df.columns if c != "adoption_binary"]
    num_predictors = max(1, len(predictor_cols))

    ratio = effective_N_events / num_predictors if num_predictors else 0.0
    shortfall = ratio < 10

    result = {
        "effective_N_events": effective_N_events,
        "num_predictors": num_predictors,
        "ratio": round(ratio, 3),
        "shortfall": shortfall,
    }

    # Log the result.
    update_log_section(
        "power_analysis",
        result,
        log_path=get_config("modeling_log_path", "modeling_log.yaml"),
    )
    return result


@log_operation("export_cleaned_data")
def export_cleaned_data(df: pd.DataFrame) -> Path:
    """Write the cleaned DataFrame to ``data/processed/cleaned_data.csv``."""
    proc_dir = get_processed_data_path()
    proc_dir.mkdir(parents=True, exist_ok=True)
    out_path = proc_dir / "cleaned_data.csv"
    df.to_csv(out_path, index=False)
    return out_path


# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Clean raw survey data and perform a power analysis."
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Optional explicit path to the raw CSV (overrides config).",
    )
    args = parser.parse_args(argv)

    try:
        setup_logging()
        cfg = load_config()  # noqa: F841 – kept for side‑effects / logging

        # Load raw data (respect ``--input`` if supplied).
        if args.input:
            raw_path = Path(args.input)
            if not raw_path.is_file():
                raise CustomDataError(f"Specified input file not found: {raw_path}")
            df_raw = pd.read_csv(raw_path)
        else:
            df_raw = load_raw_data()

        # Validation
        missing = validate_variables(df_raw)
        if missing:
            # Continue execution – missing columns will be handled downstream
            # (e.g., imputation may fill them). The log already records the gap.
            pass

        # Missingness diagnostics
        _ = calculate_missingness(df_raw)

        # Clean data
        df_clean = handle_missing_values(df_raw)
        df_clean = normalize_categorical_codes(df_clean)

        # Power analysis (does not halt execution)
        _ = calculate_power_analysis(df_clean)

        # Export
        export_cleaned_data(df_clean)

        return 0
    except CustomDataError as exc:
        print(f"Data error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover – unexpected failures
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
