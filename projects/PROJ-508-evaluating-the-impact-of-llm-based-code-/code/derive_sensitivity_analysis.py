"""
Sensitivity Analysis Derivation Script.

This script performs a sensitivity analysis by sweeping the `iteration_count`
threshold over a range of low integer values and recording the effect estimates
of the LLM adoption flag on the outcome.

It reads the master dataset, runs the statistical model for each threshold,
and writes the results to `data/derived/sensitivity_analysis.json`.
"""
import json
import logging
from pathlib import Path
import sys
import os
import pandas as pd
import numpy as np
from statsmodels.formula.api import glmmPQL
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_master_dataset():
    """Load the master dataset from the derived directory."""
    config = get_config()
    path = Path(config['paths']['derived_dir']) / 'master_dataset.csv'
    if not path.exists():
        raise FileNotFoundError(f"Master dataset not found at {path}")
    logger.info(f"Loading master dataset from {path}")
    return pd.read_csv(path)

def run_sensitivity_sweep(df, threshold_range):
    """
    Run the sensitivity analysis by sweeping the iteration_count threshold.

    Args:
        df (pd.DataFrame): The master dataset.
        threshold_range (list): List of integer thresholds to test.

    Returns:
        dict: Results containing coefficients, standard errors, and p-values for each threshold.
    """
    results = []
    logger.info(f"Starting sensitivity sweep over thresholds: {threshold_range}")

    for threshold in threshold_range:
        logger.info(f"Processing threshold: {threshold}")
        
        # Filter data based on the threshold
        # We keep rows where iteration_count >= threshold
        # This simulates the effect of ignoring very low iteration counts (noise)
        filtered_df = df[df['iteration_count'] >= threshold].copy()
        
        if filtered_df.empty:
            logger.warning(f"No data remaining for threshold {threshold}. Skipping.")
            results.append({
                "threshold": threshold,
                "n_observations": 0,
                "llm_adoption_coef": None,
                "llm_adoption_se": None,
                "llm_adoption_pvalue": None,
                "error": "No data remaining"
            })
            continue

        # Prepare the formula
        # Model: iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity
        # We use a GLMM with random intercepts for repository_id
        # Note: Since iteration_count is count data and likely overdispersed, 
        # we might use a Negative Binomial or Poisson family. 
        # However, for simplicity and consistency with the main analysis, 
        # we will use a Gaussian family with a log link if possible, or just Gaussian.
        # Given the constraints of statsmodels in this environment, we'll use GLMMPQL with Gaussian.
        
        # Check for zero-inflation or other issues if necessary, but for now, proceed with standard GLMM.
        # If iteration_count has many zeros, a ZINB might be better, but we are focusing on the sweep.
        
        formula = "iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity"
        
        try:
            # Fit the model
            # Using GLMMPQL for mixed effects with non-Gaussian families if needed, 
            # but for now, let's try GEE which is more robust for this structure in statsmodels
            # or standard GLM if mixed effects are too heavy.
            # The spec asks for Mixed-Effects Models (GLMM).
            # statsmodels doesn't have a direct GLMM for Negative Binomial easily accessible without extra packages.
            # We will use GEE as an approximation for the random intercepts (Exchangeable correlation)
            # or try to use the 'glmmPQL' from R via rpy2 if available, but assuming Python only.
            # Let's use GEE with Exchangeable correlation structure as a proxy for random intercepts.
            
            # Ensure data types are correct
            filtered_df['llm_adoption_flag'] = filtered_df['llm_adoption_flag'].astype(int)
            
            # Fit GEE model
            # family=sm.families.Gaussian() (default)
            # We might need to transform iteration_count if it's highly skewed, but let's try raw first.
            import statsmodels.api as sm
            
            # Handle potential missing values
            model_data = filtered_df.dropna(subset=['iteration_count', 'llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity', 'repository_id'])
            
            if len(model_data) < 10:
                logger.warning(f"Not enough data points after dropping NaNs for threshold {threshold}. Skipping.")
                results.append({
                    "threshold": threshold,
                    "n_observations": len(model_data),
                    "llm_adoption_coef": None,
                    "llm_adoption_se": None,
                    "llm_adoption_pvalue": None,
                    "error": "Insufficient data after dropping NaNs"
                })
                continue

            # Define the formula and group
            # Using GEE for random intercepts approximation
            gee_model = GEE(
                model_data['iteration_count'],
                model_data[['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']],
                groups=model_data['repository_id'],
                cov_struct=Exchangeable()
            )
            
            # If iteration_count is count data, we should ideally use Poisson or Negative Binomial family.
            # Let's try Poisson family for count data.
            try:
                gee_model = GEE(
                    model_data['iteration_count'],
                    model_data[['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']],
                    groups=model_data['repository_id'],
                    cov_struct=Exchangeable(),
                    family=sm.families.Poisson()
                )
                result = gee_model.fit()
            except Exception as e:
                logger.warning(f"Poisson family failed for threshold {threshold}: {e}. Falling back to Gaussian.")
                gee_model = GEE(
                    model_data['iteration_count'],
                    model_data[['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']],
                    groups=model_data['repository_id'],
                    cov_struct=Exchangeable(),
                    family=sm.families.Gaussian()
                )
                result = gee_model.fit()

            # Extract results for llm_adoption_flag
            # The coefficients are in result.params
            # The standard errors are in result.bse
            # The p-values are in result.pvalues
            
            coef_idx = result.model.exog_names.index('llm_adoption_flag')
            coef = result.params[coef_idx]
            se = result.bse[coef_idx]
            pval = result.pvalues[coef_idx]

            results.append({
                "threshold": threshold,
                "n_observations": len(model_data),
                "llm_adoption_coef": float(coef),
                "llm_adoption_se": float(se),
                "llm_adoption_pvalue": float(pval),
                "error": None
            })

        except Exception as e:
            logger.error(f"Error processing threshold {threshold}: {e}", exc_info=True)
            results.append({
                "threshold": threshold,
                "n_observations": len(filtered_df),
                "llm_adoption_coef": None,
                "llm_adoption_se": None,
                "llm_adoption_pvalue": None,
                "error": str(e)
            })

    return results

def write_sensitivity_results(results, output_path):
    """Write the sensitivity analysis results to a JSON file."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sensitivity analysis results written to {output_path}")

def main():
    """Main entry point for the sensitivity analysis script."""
    logger.info("Starting Sensitivity Analysis Pipeline")
    
    try:
        # Load data
        df = load_master_dataset()
        
        # Define the threshold range (low integers as per task description)
        # Sweep from 1 to 10, for example
        threshold_range = list(range(1, 11))
        
        # Run the sweep
        results = run_sensitivity_sweep(df, threshold_range)
        
        # Write results
        config = get_config()
        output_path = Path(config['paths']['derived_dir']) / 'sensitivity_analysis.json'
        write_sensitivity_results(results, output_path)
        
        logger.info("Sensitivity Analysis Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()