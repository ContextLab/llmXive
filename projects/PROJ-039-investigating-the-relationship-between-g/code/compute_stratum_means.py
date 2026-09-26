"""
T015: Compute final stratum features from raw aggregation.

This script implements the Ecological Aggregation post-processing step:
1. Load `data/processed/raw_stratum_agg.csv` (produced by T014).
2. Compute mean alpha power per stratum.
3. Compute mean taxa abundances per stratum.
4. Apply CLR transformation to mean taxa abundances (with pseudocount=0.5).
5. Output `data/processed/stratum_features.csv`.

Dependencies:
- T014 must have exited successfully (valid_strata_count >= 5).
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import project utilities
from config import get_project_root
from logging_config import get_analysis_logger, log_structured_event
from seed_manager import set_seed

# Set seed for reproducibility
set_seed(42)

# Constants
PSEUDOCOUNT = 0.5
PROJECT_ROOT = get_project_root()
RAW_AGG_PATH = PROJECT_ROOT / "data" / "processed" / "raw_stratum_agg.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "stratum_features.csv"
STRATA_REPORT_PATH = PROJECT_ROOT / "artifacts" / "strata_report.json"

logger = get_analysis_logger()


def load_raw_stratum_data() -> pd.DataFrame:
    """
    Load the raw stratum aggregation file produced by T014.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not RAW_AGG_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {RAW_AGG_PATH}. "
            "Ensure T014 (ecological_aggregation.py) has run successfully."
        )

    df = pd.read_csv(RAW_AGG_PATH)

    required_cols = ["stratum_id", "n_subjects", "mean_alpha_power", "taxa_means"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {RAW_AGG_PATH}: {missing}")

    logger.info(f"Loaded raw stratum data with {len(df)} rows from {RAW_AGG_PATH}")
    return df


def compute_stratum_means(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute final stratum features.

    The input 'taxa_means' column is expected to be a string representation
    of a dictionary (JSON) or a Series of dicts. We normalize it to a dict per row.
    """
    # Ensure taxa_means is a dict per row
    if df["taxa_means"].dtype == object:
        # If it's a string representation of a dict, parse it
        if isinstance(df["taxa_means"].iloc[0], str):
            df["taxa_means"] = df["taxa_means"].apply(json.loads)
        elif isinstance(df["taxa_means"].iloc[0], dict):
            pass
        else:
            raise ValueError(f"Unexpected type for 'taxa_means': {type(df['taxa_means'].iloc[0])}")

    # Extract all unique taxa names across all strata to form columns
    all_taxa = set()
    for taxa_dict in df["taxa_means"]:
        all_taxa.update(taxa_dict.keys())
    all_taxa = sorted(list(all_taxa))

    # Create a DataFrame for taxa abundances
    taxa_df = pd.DataFrame(
        df["taxa_means"].tolist(),
        index=df.index,
        columns=all_taxa
    ).fillna(0.0)

    # Store mean_alpha_power and n_subjects separately
    result_df = pd.DataFrame({
        "stratum_id": df["stratum_id"],
        "mean_alpha_power": df["mean_alpha_power"],
        "n_subjects": df["n_subjects"]
    })

    # Attach CLR transformed taxa abundances
    clr_df = apply_clr_to_stratum_means(taxa_df)

    # Merge CLR data into result
    for col in clr_df.columns:
        result_df[f"clr_{col}"] = clr_df[col]

    # Store the original mean abundances as a JSON string for reference (optional but useful)
    # But the spec asks for CLR in the output dict. Let's format the output as requested.
    # The spec says: "Output: Write `data/processed/stratum_features.csv` containing
    # `stratum_id`, `mean_alpha_power`, `clr_taxa_abundances` (dict), and `n_subjects`."

    # We will store the CLR dict as a JSON string in a column named 'clr_taxa_abundances'
    result_df["clr_taxa_abundances"] = result_df.apply(
        lambda row: json.dumps({
            col.replace("clr_", ""): float(row[col])
            for col in result_df.columns
            if col.startswith("clr_")
        }),
        axis=1
    )

    # Select final columns
    final_cols = ["stratum_id", "mean_alpha_power", "clr_taxa_abundances", "n_subjects"]
    return result_df[final_cols]


def clr_transform(abundances: np.ndarray) -> np.ndarray:
    """
    Apply Centered Log-Ratio (CLR) transformation to an array of abundances.

    Formula: clr = log((x + pseudocount) / geometric_mean(x + pseudocount))

    Args:
        abundances: 1D numpy array of abundances.

    Returns:
        1D numpy array of CLR-transformed values.
    """
    x = abundances + PSEUDOCOUNT
    # Avoid log(0) by ensuring x > 0 (guaranteed by pseudocount)
    log_x = np.log(x)
    geometric_mean_log = np.mean(log_x)
    return log_x - geometric_mean_log


def apply_clr_to_stratum_means(taxa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply CLR transformation to each row (stratum) of the taxa DataFrame.

    Args:
        taxa_df: DataFrame where rows are strata and columns are taxa.

    Returns:
        DataFrame of CLR-transformed values.
    """
    clr_data = taxa_df.apply(
        lambda row: clr_transform(row.values),
        axis=1
    )
    clr_df = pd.DataFrame(
        clr_data.tolist(),
        index=taxa_df.index,
        columns=[f"clr_{col}" for col in taxa_df.columns]
    )
    return clr_df


def format_output(df: pd.DataFrame) -> None:
    """
    Log summary statistics of the output.
    """
    logger.info(f"Output shape: {df.shape}")
    logger.info(f"Number of strata: {len(df)}")
    logger.info(f"Number of taxa processed: {len([c for c in df.columns if c.startswith('clr_')])}")
    logger.info(f"Mean alpha power range: [{df['mean_alpha_power'].min():.4f}, {df['mean_alpha_power'].max():.4f}]")


def main():
    """
    Main entry point for T015.
    """
    logger.info("Starting T015: Compute Stratum Means")

    try:
        # 1. Load raw stratum data
        raw_df = load_raw_stratum_data()

        # 2. Verify T014 exit condition (valid_strata_count >= 5)
        if STRATA_REPORT_PATH.exists():
            with open(STRATA_REPORT_PATH, "r") as f:
                report = json.load(f)
            valid_count = report.get("valid_strata_count", 0)
            if valid_count < 5:
                logger.error(f"Insufficient valid strata ({valid_count}) for ecological analysis. T014 should have exited.")
                sys.exit(1)
        else:
            logger.warning(f"Strata report not found at {STRATA_REPORT_PATH}. Proceeding with caution.")

        # 3. Compute stratum means and apply CLR
        final_df = compute_stratum_means(raw_df)

        # 4. Format and log summary
        format_output(final_df)

        # 5. Write output to disk
        final_df.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Successfully wrote output to {OUTPUT_PATH}")

        # Log structured event for completion
        log_structured_event(
            event_type="task_complete",
            task_id="T015",
            status="success",
            output_file=str(OUTPUT_PATH),
            row_count=len(final_df)
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during T015 execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()