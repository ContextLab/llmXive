"""
Secondary LMM fitting script using statsmodels (Wald-Z statistics).

This script fits a Linear Mixed Model to the analysis-ready data to provide
a comparison against the primary Satterthwaite (R) implementation.
It uses statsmodels.MixedLM with Wald Z-statistics for p-values.

Output: data/results/lmm_summary_wald.csv
"""

import csv
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

from config import get_processed_data_dir, get_results_dir
from logging_config import setup_logging, get_logger

# Ensure logging is configured
setup_logging()
logger = get_logger(__name__)

# Input/Output paths
INPUT_FILENAME = "analysis_ready.csv"
OUTPUT_FILENAME = "lmm_summary_wald.csv"

def get_input_path() -> Path:
    return get_processed_data_dir() / INPUT_FILENAME

def get_output_path() -> Path:
    return get_results_dir() / OUTPUT_FILENAME

def load_analysis_ready_data(path: Path) -> pd.DataFrame:
    """Load the analysis-ready dataset."""
    if not path.is_file():
        logger.error(f"Input file not found: {path}")
        raise FileNotFoundError(f"Input file not found: {path}")
    
    logger.info(f"Loading data from {path}")
    df = pd.read_csv(path)
    
    # Ensure categorical columns are treated as such
    if 'relationship_context' in df.columns:
        df['relationship_context'] = df['relationship_context'].astype('category')
    if 'cue_intensity_group' in df.columns:
        df['cue_intensity_group'] = df['cue_intensity_group'].astype('category')
        
    return df

def fit_wald_lmm(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a Linear Mixed Model using statsmodels MixedLM (Wald-Z).
    
    Model Formula (example based on typical design):
    rating ~ relationship_context * cue_intensity_group + (1 | participant_id)
    
    Returns a dictionary of results suitable for serialization.
    """
    # Define model formula
    # Assuming columns: 'rating', 'relationship_context', 'cue_intensity_group', 'participant_id'
    # If columns differ, this will raise an error, which is appropriate for validation.
    formula = "rating ~ relationship_context * cue_intensity_group"
    re_formula = "1"
    groups = "participant_id"

    try:
        # Fit the model
        # statsmodels MixedLM uses REML by default, but for Wald Z we often look at the summary
        model = MixedLM.from_formula(formula, groups=groups, re_formula=re_formula, data=df)
        result = model.fit()
        
        # Extract fixed effects parameters
        fixed_effects = result.params
        std_errors = result.bse
        z_values = fixed_effects / std_errors
        # Two-tailed p-value for Wald Z
        p_values = 2 * (1 - sm.distributions.norm.cdf(np.abs(z_values)))
        
        # Extract variance components (random effects)
        # result.cov_re contains the covariance matrix of the random effects
        # result.scale is the residual variance
        
        summary_data = []
        for term in fixed_effects.index:
            summary_data.append({
                "term": term,
                "estimate": float(fixed_effects[term]),
                "std_error": float(std_errors[term]),
                "z_value": float(z_values[term]),
                "p_value": float(p_values[term]),
                "method": "Wald-Z (statsmodels)"
            })
        
        # Add random effect variance info
        # MixedLM returns a covariance matrix, so we take the diagonal
        # For a simple (1|group) model, this is just the variance of the intercept
        try:
            random_var = float(np.diag(result.cov_re)[0])
        except Exception:
            random_var = 0.0
        
        summary_data.append({
            "term": "random_intercept_variance",
            "estimate": random_var,
            "std_error": None,
            "z_value": None,
            "p_value": None,
            "method": "Wald-Z (statsmodels)"
        })
        
        summary_data.append({
            "term": "residual_variance",
            "estimate": float(result.scale),
            "std_error": None,
            "z_value": None,
            "p_value": None,
            "method": "Wald-Z (statsmodels)"
        })

        return summary_data

    except Exception as e:
        logger.error(f"Error fitting MixedLM: {e}")
        raise

def save_results(results: List[Dict[str, Any]], path: Path):
    """Save the results to a CSV file."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        if not results:
            logger.warning("No results to save.")
            return
        
        fieldnames = ["term", "estimate", "std_error", "z_value", "p_value", "method"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Results saved to {path}")

def main():
    """Main entry point."""
    input_path = get_input_path()
    output_path = get_output_path()

    logger.info("Starting secondary LMM fitting (Wald-Z)...")
    
    try:
        df = load_analysis_ready_data(input_path)
        logger.info(f"Data loaded: {len(df)} rows")
        
        if df.empty:
            logger.error("Dataset is empty. Cannot fit model.")
            sys.exit(1)

        results = fit_wald_lmm(df)
        save_results(results, output_path)
        
        logger.info("Secondary LMM fitting completed successfully.")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
