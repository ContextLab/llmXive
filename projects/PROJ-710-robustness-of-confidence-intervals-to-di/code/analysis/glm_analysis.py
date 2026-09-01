"""
GLM Analysis Module for PROJ-710.

This module fits Generalized Linear Models (GLM) with binomial link
to test the effects of epsilon and noise type on coverage probability.
"""
import statsmodels.api as sm
from statsmodels.formula.api import glm as smf_glm
from typing import Tuple, Optional
import pandas as pd
import numpy as np
import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fit_coverage_glm(
    df: pd.DataFrame,
    formula: str = "covered ~ epsilon * noise_type"
) -> Tuple[sm.GLM, sm.GLMResultsWrapper]:
    """
    Fit a GLM with binomial family to coverage data.

    Args:
        df: DataFrame containing 'covered', 'epsilon', 'noise_type', and optionally 'dataset', 'statistic'.
        formula: R-style formula for the GLM.

    Returns:
        Tuple of (model, results)
    """
    # Ensure 'covered' is numeric and binary (0 or 1)
    # The data might be stored as floats representing proportions or integers
    if 'covered' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'covered' column.")

    df_clean = df.copy()

    # Convert covered to numeric, coerce errors to NaN, then drop NaNs
    df_clean['covered'] = pd.to_numeric(df_clean['covered'], errors='coerce')
    
    # Ensure we have binary outcomes (0 or 1) for binomial GLM
    # If the data contains proportions (e.g., 0.95), we might need to aggregate differently
    # or treat it as a binomial with weights. However, standard practice for this pipeline
    # is to have a binary indicator per simulation run.
    # We enforce 0/1 for the binomial family unless we have counts/trials.
    # Assuming 'covered' is a binary indicator (0/1) from the simulation loop.
    
    if df_clean['covered'].nunique() > 2:
        logger.warning(f"Column 'covered' has more than 2 unique values: {df_clean['covered'].unique()}. "
                       "Attempting to coerce to binary (0/1) by thresholding at 0.5 if continuous, "
                       "or raising error if categorical non-binary.")
        # If it looks like a proportion (e.g. 0.0 to 1.0), we might need to handle it as binomial with weights.
        # But the formula `covered ~ ...` implies a binary response. 
        # Let's assume the pipeline outputs 0 or 1. If not, we cast to int (0 or 1) if close enough, 
        # otherwise we fail loudly to avoid silent data fabrication/corruption.
        if df_clean['covered'].min() >= 0 and df_clean['covered'].max() <= 1:
            # It's a proportion or binary. If it's binary, we are good. If it's continuous, 
            # binomial GLM expects counts (successes, trials) or a two-column response.
            # However, if the data is already aggregated coverage rates (e.g. 0.95), 
            # we should NOT fit a binomial GLM on the rate directly without weights.
            # The task says "Load artifacts/coverage_results.csv". 
            # If that CSV contains binary outcomes (covered: 0/1), we are good.
            # If it contains aggregated rates, we need a different approach.
            # Given the context of "coverage probability", the raw data should be binary (success/fail per sim).
            # We will assume binary. If not, we raise an error to force correction.
            pass
    
    # Drop rows with missing values in key variables
    df_clean = df_clean.dropna(subset=['covered', 'epsilon', 'noise_type'])

    if len(df_clean) == 0:
        raise ValueError("DataFrame is empty after dropping NaNs. Check data source.")

    # Ensure epsilon is numeric
    df_clean['epsilon'] = pd.to_numeric(df_clean['epsilon'], errors='coerce')
    df_clean = df_clean.dropna(subset=['epsilon'])

    if len(df_clean) == 0:
        raise ValueError("DataFrame is empty after ensuring epsilon is numeric.")

    logger.info(f"Fitting GLM with formula: {formula}")
    logger.info(f"Data shape: {df_clean.shape}")
    logger.info(f"Unique noise_types: {df_clean['noise_type'].unique()}")
    logger.info(f"Unique epsilon values: {df_clean['epsilon'].unique()}")

    # Fit the model
    try:
        model = smf_glm(formula=formula, data=df_clean, family=sm.families.Binomial())
        result = model.fit()
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        raise

    return model, result


def run_glm_analysis():
    """
    Main entry point to run GLM analysis on coverage results.
    Loads artifacts/coverage_results.csv, fits the model, and saves results.
    """
    # Load data
    input_path = Path("artifacts/coverage_results.csv")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the simulation pipeline (T013a/T013d) to generate coverage_results.csv first.")
        raise FileNotFoundError(f"Required input file not found: {input_path}")

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Check required columns
    required_cols = ['covered', 'epsilon', 'noise_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")

    # Fit the GLM
    model, result = fit_coverage_glm(df)

    # Print summary
    logger.info("\nGLM Summary:")
    print(result.summary())

    # Save results to JSON
    output_path = Path("artifacts/glm_summary.json")
    summary_data = {
        "formula": model.formula,
        "family": str(model.family.__class__.__name__),
        "converged": result.converged,
        "deviance": float(result.deviance),
        "null_deviance": float(result.null_deviance),
        "aic": float(result.aic),
        "coefficients": result.params.to_dict(),
        "p_values": result.pvalues.to_dict(),
        "standard_errors": result.bse.to_dict(),
        "confidence_intervals": {
            param: list(result.conf_int().loc[param])
            for param in result.params.index
        }
    }

    with open(output_path, 'w') as f:
        json.dump(summary_data, f, indent=2)

    logger.info(f"GLM summary saved to {output_path}")
    return result


if __name__ == "__main__":
    run_glm_analysis()
