"""
Uncertainty Calculator Module for Perovskite Stability Analysis.

Computes total uncertainty for T_d values by combining instrument precision
and experimental error using the root-sum-square method.
"""
import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PRECISION = 10.0  # ±10°C default for missing instrument precision
DEFAULT_EXPERIMENTAL_ERROR = 0.0  # Default for missing experimental error
EXCLUSION_LOG_PATH = Path("data/processed/exclusion_log.csv")
OUTPUT_PATH = Path("data/processed/descriptors_uncertainty.csv")
INPUT_PATH = Path("data/raw/perovskites_merged.csv")


def calculate_total_uncertainty(
    instrument_precision: Optional[float],
    experimental_error: Optional[float],
    formula: str,
    source: str,
) -> Tuple[Optional[float], str]:
    """
    Calculate total uncertainty using root-sum-square method.

    Formula: sigma_total = sqrt(precision^2 + experimental_error^2)

    Args:
        instrument_precision: Precision from instrument registry or source (±°C).
        experimental_error: Reported experimental error from source metadata.
        formula: Chemical formula for logging.
        source: Data source identifier (e.g., 'NREL', 'MaterialsProject').

    Returns:
        Tuple of (total_uncertainty, log_message).
        If total_uncertainty is NaN or missing, returns (None, exclusion_reason).
    """
    # Apply defaults and log warnings
    if instrument_precision is None or (
        isinstance(instrument_precision, float) and math.isnan(instrument_precision)
    ):
        logger.warning(
            f"Missing instrument precision for {formula} (source: {source}). "
            f"Using default ±{DEFAULT_PRECISION}°C."
        )
        instrument_precision = DEFAULT_PRECISION
    elif instrument_precision < 0:
        logger.warning(
            f"Negative instrument precision ({instrument_precision}) for {formula}. "
            f"Using absolute value."
        )
        instrument_precision = abs(instrument_precision)

    if experimental_error is None or (
        isinstance(experimental_error, float) and math.isnan(experimental_error)
    ):
        logger.debug(
            f"Missing experimental error for {formula} (source: {source}). "
            f"Using default 0.0."
        )
        experimental_error = DEFAULT_EXPERIMENTAL_ERROR
    elif experimental_error < 0:
        logger.warning(
            f"Negative experimental error ({experimental_error}) for {formula}. "
            f"Using absolute value."
        )
        experimental_error = abs(experimental_error)

    # Calculate combined uncertainty
    try:
        total_uncertainty = math.sqrt(
            instrument_precision**2 + experimental_error**2
        )
    except (ValueError, OverflowError) as e:
        logger.error(
            f"Error calculating uncertainty for {formula}: {e}. "
            "Marking for exclusion."
        )
        return None, f"Calculation error: {e}"

    # Check for NaN or infinite results
    if math.isnan(total_uncertainty) or math.isinf(total_uncertainty):
        logger.warning(
            f"Invalid total uncertainty ({total_uncertainty}) for {formula}. "
            "Marking for exclusion."
        )
        return None, f"Invalid uncertainty value: {total_uncertainty}"

    return total_uncertainty, "Success"


def compute_uncertainties_for_dataframe(
    df: pd.DataFrame,
    precision_col: str = "temperature_precision",
    experimental_error_col: str = "experimental_error",
    formula_col: str = "formula",
    source_col: str = "source",
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Compute total uncertainty for all rows in a DataFrame.

    Args:
        df: Input DataFrame with T_d and metadata columns.
        precision_col: Column name for instrument precision.
        experimental_error_col: Column name for experimental error.
        formula_col: Column name for chemical formula.
        source_col: Column name for data source.

    Returns:
        Tuple of (DataFrame with 'total_uncertainty' column, list of exclusion records).
    """
    exclusion_records = []
    total_uncertainties = []

    for idx, row in df.iterrows():
        formula = row.get(formula_col, "Unknown")
        source = row.get(source_col, "Unknown")
        precision = row.get(precision_col)
        exp_error = row.get(experimental_error_col)

        total_unc, status = calculate_total_uncertainty(
            precision, exp_error, formula, source
        )

        if total_unc is not None:
            total_uncertainties.append(total_unc)
        else:
            total_uncertainties.append(None)
            exclusion_records.append({
                "formula": formula,
                "source": source,
                "reason": status,
                "precision_value": precision,
                "experimental_error_value": exp_error,
            })
            logger.info(f"Excluding entry: {formula} from {source}. Reason: {status}")

    # Create new DataFrame with uncertainty column
    result_df = df.copy()
    result_df["total_uncertainty"] = total_uncertainties

    return result_df, exclusion_records


def save_exclusion_log(exclusion_records: List[Dict], output_path: Path) -> None:
    """Save exclusion log to CSV."""
    if not exclusion_records:
        logger.info("No entries to exclude. Skipping exclusion log creation.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_df = pd.DataFrame(exclusion_records)
    exclusion_df.to_csv(output_path, index=False)
    logger.info(f"Saved exclusion log to {output_path} ({len(exclusion_records)} entries)")


def main() -> None:
    """Main entry point for uncertainty calculation."""
    logger.info("Starting uncertainty calculation for perovskite dataset.")

    # Verify input file exists
    if not INPUT_PATH.exists():
        logger.error(f"Input file not found: {INPUT_PATH}")
        logger.error("Please ensure T012e (merge datasets) has completed successfully.")
        sys.exit(1)

    # Load input data
    try:
        df = pd.read_csv(INPUT_PATH)
        logger.info(f"Loaded {len(df)} rows from {INPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    # Verify required columns
    required_cols = ["formula", "source"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input data: {missing_cols}")
        sys.exit(1)

    # Compute uncertainties
    result_df, exclusion_records = compute_uncertainties_for_dataframe(
        df,
        precision_col="temperature_precision",
        experimental_error_col="experimental_error",
        formula_col="formula",
        source_col="source",
    )

    # Filter out rows with invalid uncertainty if needed (optional, based on downstream needs)
    # For now, we keep them but mark as NaN for downstream filtering
    valid_count = result_df["total_uncertainty"].notna().sum()
    logger.info(f"Computed uncertainties for {valid_count}/{len(result_df)} entries.")

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved uncertainty-enhanced dataset to {OUTPUT_PATH}")

    # Save exclusion log
    save_exclusion_log(exclusion_records, EXCLUSION_LOG_PATH)

    logger.info("Uncertainty calculation completed successfully.")


if __name__ == "__main__":
    main()
