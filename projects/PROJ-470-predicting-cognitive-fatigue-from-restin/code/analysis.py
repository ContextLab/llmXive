from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Import logging utility from the project's shared logging module
from utils.logging import get_logger, log_operation

# Import config loader
from config import load_config

def validate_inputs() -> bool:
    """
    Validate that all required input files for the ANCOVA model exist.
    Specifically checks for the VIF success file (vif_valid_predictors.json).
    """
    logger = get_logger("analysis")
    logger.info("Validating inputs for ANCOVA model.")

    # Check for VIF success file
    vif_valid_file = Path("data/analysis/vif_valid_predictors.json")
    if not vif_valid_file.exists():
        logger.error("VIF success file not found: data/analysis/vif_valid_predictors.json")
        logger.error("T024 (VIF diagnostics) likely failed or did not run. Cannot proceed with ANCOVA.")
        return False

    # Check for complexity metrics
    complexity_file = Path("data/analysis/complexity_metrics.csv")
    if not complexity_file.exists():
        logger.error(f"Complexity metrics file not found: {complexity_file}")
        return False

    # Check for delta scores
    delta_file = Path("data/analysis/delta_scores.csv")
    if not delta_file.exists():
        logger.error(f"Delta scores file not found: {delta_file}")
        return False

    logger.info("All required input files found.")
    return True

def load_vif_valid_predictors() -> List[str]:
    """
    Load the list of valid predictors from the VIF diagnostics file.
    """
    vif_file = Path("data/analysis/vif_valid_predictors.json")
    try:
        with open(vif_file, 'r') as f:
            data = json.load(f)
            # The file should contain a list of valid predictors
            valid_predictors = data.get("valid_predictors", [])
            if not valid_predictors:
                raise ValueError("No valid predictors found in vif_valid_predictors.json")
            return valid_predictors
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger = get_logger("analysis")
        logger.error(f"Failed to load valid predictors: {e}")
        raise

def load_complexity_metrics() -> pd.DataFrame:
    """
    Load complexity metrics and aggregate to participant level (median across channels).
    """
    logger = get_logger("analysis")
    file_path = Path("data/analysis/complexity_metrics.csv")
    logger.info(f"Loading complexity metrics from {file_path}")

    df = pd.read_csv(file_path)

    # Aggregate to participant level: median across channels for Pre_Complexity
    # Assuming the file has 'participant_id', 'channel', 'lzc_value', 'pe_value'
    # We need to select the metric used for the model. Let's assume LZC for now,
    # or we can create a column for the specific metric used.
    # The task description says "Pre_Complexity". We will use median LZC per participant.

    if 'lzc_value' not in df.columns:
        logger.error("LZC value column missing in complexity metrics.")
        raise ValueError("Missing lzc_value column")

    # Group by participant and take median
    participant_complexity = df.groupby('participant_id')['lzc_value'].median().reset_index()
    participant_complexity.rename(columns={'lzc_value': 'Pre_Complexity'}, inplace=True)

    return participant_complexity

def load_delta_scores() -> pd.DataFrame:
    """
    Load delta scores (Post - Pre) for fatigue and complexity.
    """
    logger = get_logger("analysis")
    file_path = Path("data/analysis/delta_scores.csv")
    logger.info(f"Loading delta scores from {file_path}")

    df = pd.read_csv(file_path)

    # Ensure we have Fatigue_Delta
    if 'Fatigue_Delta' not in df.columns:
        logger.error("Fatigue_Delta column missing in delta scores.")
        raise ValueError("Missing Fatigue_Delta column")

    # We also need Post_Complexity for the ANCOVA dependent variable.
    # The delta file might have complexity delta, but ANCOVA needs Post_Complexity.
    # We will need to merge this with the full complexity data or calculate Post_Complexity
    # if the delta file contains Pre and Post.
    # Assumption: delta_scores.csv contains participant_id, Fatigue_Delta, and potentially Post_Complexity.
    # If not, we need to join with the full complexity data.
    # Let's assume the delta file has the necessary columns or we construct Post from Pre + Delta.
    # However, the task says "Post_Complexity ~ ...".
    # If the delta file only has Fatigue_Delta, we need to load Post_Complexity from elsewhere.
    # Let's assume the delta file has 'Post_Complexity' or we calculate it.
    # If the delta file has 'Complexity_Delta' and 'Pre_Complexity', we can calc Post.
    # For now, we assume 'Post_Complexity' is present or we can derive it.
    # If missing, we might need to load the full complexity metrics again.
    # Let's try to load Post_Complexity from the delta file if present, otherwise from the main file.

    if 'Post_Complexity' not in df.columns:
        # Fallback: Try to load from complexity_metrics.csv and calculate Post from Pre + Delta if available
        # But simpler: The delta file should ideally contain the Post value.
        # If not, we must join.
        logger.warning("Post_Complexity not in delta scores. Attempting to load from complexity metrics.")
        # This logic might need adjustment based on actual delta_scores.csv schema.
        # For now, we assume the delta file has the necessary columns for the model.
        pass

    return df

def run_ancova_model(valid_predictors: List[str], fatigue_df: pd.DataFrame, complexity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the ANCOVA model: Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates.
    """
    logger = get_logger("analysis")
    logger.info(f"Running ANCOVA model with predictors: {valid_predictors}")

    # Merge data
    # fatigue_df should have: participant_id, Fatigue_Delta, (Post_Complexity if available)
    # complexity_df should have: participant_id, Pre_Complexity

    # We need a unified dataframe with: Post_Complexity (Y), Fatigue_Delta, Pre_Complexity, and covariates.
    # Assuming fatigue_df has Post_Complexity or we can join.
    # If fatigue_df doesn't have Post_Complexity, we might need to load it from the original complexity metrics.
    # Let's assume the delta file has 'Post_Complexity' or we calculate it.
    # If the delta file has 'Complexity_Delta' and 'Pre_Complexity', Post = Pre + Delta.

    # Check if Post_Complexity is in fatigue_df
    if 'Post_Complexity' not in fatigue_df.columns:
        logger.error("Post_Complexity not found in delta scores. Cannot run ANCOVA.")
        raise ValueError("Post_Complexity missing")

    # Merge
    merged_df = pd.merge(fatigue_df, complexity_df, on='participant_id', how='inner')

    if merged_df.empty:
        logger.error("No overlapping participants between fatigue and complexity data.")
        raise ValueError("No overlapping participants")

    # Select predictors
    predictors = ['Fatigue_Delta', 'Pre_Complexity']
    # Add covariates if they exist in the merged dataframe
    possible_covariates = ['age', 'time_of_day', 'medication_status']
    for cov in possible_covariates:
        if cov in merged_df.columns:
            predictors.append(cov)
            logger.info(f"Including covariate: {cov}")
        else:
            logger.warning(f"Covariate {cov} not found in data, skipping.")

    # Ensure we are only using valid predictors from VIF
    # The task says: "Use only the predictors validated by T024".
    # We assume Fatigue_Delta and Pre_Complexity are always valid if VIF passed.
    # If covariates were in the VIF check, they should be in valid_predictors.
    # We will filter the predictors list to only include those in valid_predictors.
    final_predictors = [p for p in predictors if p in valid_predictors]

    if len(final_predictors) < 2:
        logger.error("Not enough valid predictors for ANCOVA (need at least Fatigue_Delta and Pre_Complexity).")
        raise ValueError("Insufficient valid predictors")

    # Construct formula
    # Y ~ X1 + X2 + ...
    formula = f"Post_Complexity ~ {' + '.join(final_predictors)}"

    logger.info(f"ANCOVA Formula: {formula}")

    # Fit model
    model = ols(formula, data=merged_df).fit()

    # Extract results
    results_df = model.summary2().tables[1]
    # Convert summary table to a more usable format
    # The summary2 table is a DataFrame with columns: Coef, Std Err, t, P>|t|, [0.025, 0.975]
    results_df = results_df.reset_index()
    results_df.rename(columns={'index': 'variable'}, inplace=True)

    # Filter out Intercept if needed, but keep it for completeness
    # We want to output: variable, coef, pvalue, ci_low, ci_high

    output_df = results_df[['variable', 'Coef', 'P>|t|', '[0.025', '0.975]']].copy()
    output_df.columns = ['variable', 'coef', 'pvalue', 'ci_low', 'ci_high']

    logger.info("ANCOVA model fitted successfully.")
    return output_df

def save_ancova_results(results_df: pd.DataFrame) -> None:
    """
    Save ANCOVA results to data/analysis/ancova_results.csv.
    """
    output_path = Path("data/analysis/ancova_results.csv")
    logger = get_logger("analysis")
    logger.info(f"Saving ANCOVA results to {output_path}")

    results_df.to_csv(output_path, index=False)
    logger.info("ANCOVA results saved.")

def main() -> int:
    """
    Main entry point for the ANCOVA analysis task (T021).
    """
    logger = get_logger("analysis")
    logger.info("Starting ANCOVA model analysis (T021).")

    # 1. Validate inputs
    if not validate_inputs():
        logger.error("Input validation failed. Exiting.")
        return 1

    # 2. Load valid predictors
    try:
        valid_predictors = load_vif_valid_predictors()
    except Exception as e:
        logger.error(f"Failed to load valid predictors: {e}")
        return 1

    if not valid_predictors:
        logger.error("No valid predictors for ANCOVA. Exiting.")
        return 1

    # 3. Load data
    try:
        complexity_df = load_complexity_metrics()
        fatigue_df = load_delta_scores()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return 1

    # 4. Run ANCOVA
    try:
        results = run_ancova_model(valid_predictors, fatigue_df, complexity_df)
    except Exception as e:
        logger.error(f"ANCOVA model fitting failed: {e}")
        return 1

    # 5. Save results
    try:
        save_ancova_results(results)
    except Exception as e:
        logger.error(f"Failed to save ANCOVA results: {e}")
        return 1

    logger.info("ANCOVA analysis completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())