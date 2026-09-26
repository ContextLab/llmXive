"""
Compute final stratum features from raw aggregated data.

This script performs the following steps:
1. Load `data/processed/raw_stratum_agg.csv` produced by T014.
2. Compute mean alpha power and mean taxa abundances per stratum.
3. Apply Centered Log-Ratio (CLR) transformation to taxa abundances with a pseudocount of 0.5.
4. Output `data/processed/stratum_features.csv` containing stratum_id, mean_alpha_power,
   clr_taxa_abundances (as a JSON string or flattened columns), and n_subjects.

Dependencies:
- T014 (ecological_aggregation.py) must have completed successfully (exit code 0).
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from project modules to ensure consistency
from config import get_project_root
from logging_config import get_analysis_logger, log_structured_event
from seed_manager import set_seed

# Constants
PSEUDOCOUNT = 0.5
STRATA_INPUT_PATH = "data/processed/raw_stratum_agg.csv"
STRATA_OUTPUT_PATH = "data/processed/stratum_features.csv"
STRATA_REPORT_PATH = "artifacts/strata_report.json"

logger = get_analysis_logger(__name__)


def load_raw_stratum_data(input_path: str) -> pd.DataFrame:
    """
    Load the raw stratum aggregation CSV.

    Args:
        input_path: Path to raw_stratum_agg.csv.

    Returns:
        DataFrame with stratum data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    full_path = get_project_root() / input_path
    if not full_path.exists():
        raise FileNotFoundError(f"Required input file not found: {full_path}")

    df = pd.read_csv(full_path)
    required_cols = ["stratum_id", "alpha_power", "taxa_abundances", "n_subjects"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")

    logger.info(f"Loaded raw stratum data: {len(df)} strata from {full_path}")
    return df


def compute_stratum_means(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mean alpha power and mean taxa abundances per stratum.

    The input 'alpha_power' column is expected to be a list of values per stratum
    (or a single value if pre-aggregated). The 'taxa_abundances' column is expected
    to be a JSON string or a dict of genus -> abundance.

    We assume the input from T014 provides lists of values or pre-calculated means.
    If lists are provided, we compute the mean here. If single values, we keep them.

    Args:
        df: DataFrame from load_raw_stratum_data.

    Returns:
        DataFrame with computed means.
    """
    result_rows = []

    for _, row in df.iterrows():
        stratum_id = row["stratum_id"]
        n_subjects = row["n_subjects"]

        # Handle alpha_power: could be a list or a scalar
        alpha_data = row["alpha_power"]
        if isinstance(alpha_data, str):
            try:
                alpha_data = json.loads(alpha_data)
            except json.JSONDecodeError:
                alpha_data = [float(alpha_data)]
        
        if isinstance(alpha_data, list):
            mean_alpha = np.mean(alpha_data)
        else:
            mean_alpha = float(alpha_data)

        # Handle taxa_abundances: could be a JSON string dict or a dict
        taxa_data = row["taxa_abundances"]
        if isinstance(taxa_data, str):
            try:
                taxa_mean = json.loads(taxa_data)
            except json.JSONDecodeError:
                taxa_mean = {}
        elif isinstance(taxa_data, dict):
            taxa_mean = taxa_data
        else:
            logger.warning(f"Unexpected taxa_abundances type for {stratum_id}: {type(taxa_data)}")
            taxa_mean = {}

        result_rows.append({
            "stratum_id": stratum_id,
            "mean_alpha_power": mean_alpha,
            "taxa_mean_abundances": taxa_mean,
            "n_subjects": n_subjects
        })

    return pd.DataFrame(result_rows)


def clr_transform(abundances: Dict[str, float], pseudocount: float = PSEUDOCOUNT) -> Dict[str, float]:
    """
    Apply Centered Log-Ratio (CLR) transformation to a dictionary of abundances.

    Formula: clr = log((abundance + pseudocount) / geometric_mean(all abundances + pseudocount))

    Args:
        abundances: Dict of taxon -> abundance.
        pseudocount: Value to add before log transformation.

    Returns:
        Dict of taxon -> clr_transformed value.
    """
    if not abundances:
        return {}

    values = np.array(list(abundances.values()))
    # Add pseudocount
    values_pc = values + pseudocount

    # Calculate geometric mean
    # Geometric mean = exp(mean(log(x)))
    # Handle zeros or negative values if any (shouldn't happen with pseudocount)
    if np.any(values_pc <= 0):
        logger.warning("Non-positive values detected after pseudocount addition. Setting to small epsilon.")
        values_pc = np.maximum(values_pc, 1e-10)

    log_values = np.log(values_pc)
    geometric_mean = np.exp(np.mean(log_values))

    if geometric_mean == 0:
        # Fallback if geometric mean is zero (should be impossible with pseudocount)
        logger.warning("Geometric mean is zero. Skipping CLR for this stratum.")
        return {k: 0.0 for k in abundances}

    clr_values = np.log(values_pc / geometric_mean)

    return dict(zip(abundances.keys(), clr_values))


def apply_clr_to_stratum_means(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply CLR transformation to the 'taxa_mean_abundances' column of the DataFrame.

    Args:
        df: DataFrame from compute_stratum_means.

    Returns:
        DataFrame with a new column 'clr_taxa_abundances'.
    """
    df["clr_taxa_abundances"] = df["taxa_mean_abundances"].apply(
        lambda x: clr_transform(x, PSEUDOCOUNT)
    )
    return df


def format_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format the output DataFrame for saving to CSV.
    The 'clr_taxa_abundances' column will be stored as a JSON string to fit in CSV.

    Args:
        df: DataFrame with CLR transformed data.

    Returns:
        Formatted DataFrame.
    """
    # Convert dict to JSON string for CSV compatibility
    df["clr_taxa_abundances"] = df["clr_taxa_abundances"].apply(json.dumps)
    
    # Select and order columns
    output_cols = ["stratum_id", "mean_alpha_power", "clr_taxa_abundances", "n_subjects"]
    # Ensure all columns exist
    for col in output_cols:
        if col not in df.columns:
            df[col] = None
    
    return df[output_cols]


def main():
    """Main entry point for T015."""
    set_seed(42)  # Ensure reproducibility
    
    project_root = get_project_root()
    input_path = project_root / STRATA_INPUT_PATH
    output_path = project_root / STRATA_OUTPUT_PATH
    report_path = project_root / STRATA_REPORT_PATH

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting T015: Compute Stratum Means")

    try:
        # Check if T014 produced the required input
        if not input_path.exists():
            logger.error(f"Input file {input_path} not found. T014 may have failed or not run.")
            sys.exit(1)

        # Check if T014 reported <5 valid strata
        if report_path.exists():
            with open(report_path, 'r') as f:
                report = json.load(f)
                valid_strata_count = report.get("valid_strata_count", 0)
                if valid_strata_count < 5:
                    logger.error("T014 reported <5 valid strata. Aborting T015 as per Spec.")
                    sys.exit(1)

        # 1. Load raw stratum data
        df_raw = load_raw_stratum_data(STRATA_INPUT_PATH)

        # 2. Compute means
        df_means = compute_stratum_means(df_raw)

        # 3. Apply CLR transformation
        df_clr = apply_clr_to_stratum_means(df_means)

        # 4. Format output
        df_final = format_output(df_clr)

        # 5. Save to CSV
        df_final.to_csv(output_path, index=False)
        
        log_structured_event(
            event_type="task_completion",
            task_id="T015",
            status="success",
            message=f"Successfully computed stratum means and saved to {output_path}",
            details={
                "input_rows": len(df_raw),
                "output_rows": len(df_final),
                "pseudocount": PSEUDOCOUNT
            }
        )
        
        logger.info(f"T015 complete. Output saved to {output_path}")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in T015: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()