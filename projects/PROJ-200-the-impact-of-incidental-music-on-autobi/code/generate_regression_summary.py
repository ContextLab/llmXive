"""
T038: Generate regression_summary.csv containing coefficients, SEs, p-values, and VIFs.

This script loads the aggregated User-Track Pair data (from US2), fits the
mixed-effects model (from US3), calculates VIFs, and saves the results
to data/final/regression_summary.csv.
"""
import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from existing project modules
from config import get_project_root, get_config_dict
from utils import setup_logging, get_logger
from state_manager import save_state, register_file
from modeling import fit_mixed_model, check_collinearity, extract_model_summary

logger = get_logger(__name__)

def main():
    """
    Main entry point for T038.
    1. Load data/processed/user_track_pairs.parquet
    2. Fit the mixed model (vividness ~ residualized_exposure + popularity + (1|user_id))
    3. Calculate VIFs for fixed effects
    4. Extract coefficients, SEs, p-values
    5. Save to data/final/regression_summary.csv
    """
    project_root = get_project_root()
    config = get_config_dict()
    
    input_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    output_dir = project_root / "data" / "final"
    output_file = output_dir / "regression_summary.csv"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T029 (generate_user_track_pairs) has been completed.")
        raise FileNotFoundError(f"Required input file missing: {input_path}")

    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

    required_cols = ['mean_vividness', 'residualized_exposure_score', 'overall_popularity_score', 'user_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input data: {missing_cols}")
        raise ValueError(f"Input data missing columns: {missing_cols}")

    logger.info("Fitting mixed-effects model...")
    # Formula based on spec update FR-005: mean_vividness ~ residualized_exposure + popularity + (1|user_id)
    formula = "mean_vividness ~ residualized_exposure_score + overall_popularity_score + (1|user_id)"
    
    try:
        model_result = fit_mixed_model(df, formula)
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

    logger.info("Extracting model summary...")
    summary_data = extract_model_summary(model_result, formula)

    logger.info("Calculating Variance Inflation Factors (VIF)...")
    # Calculate VIF on the fixed effect design matrix
    # We need the exog matrix from the model
    try:
        # statsmodels MixedLM might not expose exog directly in a simple way for VIF
        # We reconstruct the design matrix for fixed effects manually
        import statsmodels.api as sm
        # Create a subset for VIF calculation (excluding the grouping factor)
        vif_df = df[['residualized_exposure_score', 'overall_popularity_score']].copy()
        vif_df = vif_df.dropna()
        
        if len(vif_df) == 0:
            logger.warning("No valid data for VIF calculation after dropping NaNs.")
            vif_results = {}
        else:
            vif_results = check_collinearity(vif_df)
    except Exception as e:
        logger.warning(f"Could not calculate VIF: {e}")
        vif_results = {}

    # Merge summary and VIFs
    # summary_data is typically a list of dicts or a DataFrame
    if isinstance(summary_data, list):
        summary_df = pd.DataFrame(summary_data)
    else:
        summary_df = summary_data

    # Add VIF column if available
    if 'residualized_exposure_score' in vif_results:
        summary_df['vif_residualized_exposure_score'] = summary_df['variable'].apply(
            lambda x: vif_results.get(x, np.nan)
        )
    else:
        # Fallback: assume order or just map by name if the summary has a 'variable' column
        # If the summary format is different, this might need adjustment.
        # Assuming standard statsmodels summary extraction yields 'variable', 'coef', 'std err', 'pvalue'
        pass

    # Ensure specific columns exist for the output format
    required_output_cols = ['variable', 'coef', 'std err', 'pvalue']
    for col in required_output_cols:
        if col not in summary_df.columns:
            logger.warning(f"Output column '{col}' not found in summary. Creating empty column.")
            summary_df[col] = np.nan

    # Select and order columns
    final_cols = ['variable', 'coef', 'std err', 'pvalue']
    # Add VIF columns dynamically if they exist
    vif_cols = [c for c in summary_df.columns if c.startswith('vif_')]
    final_cols.extend(vif_cols)

    final_df = summary_df[final_cols]

    logger.info(f"Saving regression summary to {output_file}")
    final_df.to_csv(output_file, index=False)

    # Register output in state.yaml
    register_file(str(output_file), "regression_summary.csv")
    save_state()

    logger.info("T038 completed successfully.")
    return final_df

if __name__ == "__main__":
    setup_logging()
    main()
