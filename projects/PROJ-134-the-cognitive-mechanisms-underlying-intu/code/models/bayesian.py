import os
import sys
import logging
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy import stats

from code.config import init_random_seeds, get_project_root
from code.utils.logging_utils import get_logger, log_pipeline_step, log_exclusion

logger = get_logger(__name__)

def _calculate_mle_estimates(
    df: pd.DataFrame,
    target_col: str,
    predictor_cols: List[str],
    foundation_cols: List[str],
    salience_col: str
) -> Dict[str, float]:
    """
    Fallback to Maximum Likelihood Estimation (OLS) if Bayesian MCMC fails.
    Uses statsmodels to estimate parameters for the linear model:
    y ~ salience + foundations + salience*foundations
    
    Returns a dictionary of estimated coefficients.
    """
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        
        # Prepare formula: interaction term included
        # Assuming binary salience (0/1) and continuous foundation scores
        formula = f"{target_col} ~ {salience_col} + {' + '.join(foundation_cols)} + {salience_col}:{' + '.join(foundation_cols)}"
        
        # Filter out NaNs
        clean_df = df.dropna(subset=[target_col] + predictor_cols + foundation_cols + [salience_col])
        
        if len(clean_df) == 0:
            raise ValueError("No valid data points for MLE estimation.")
        
        model = smf.ols(formula=formula, data=clean_df).fit()
        
        results = {
            "method": "MLE_OLS",
            "status": "fallback",
            "coefficients": model.params.to_dict(),
            "p_values": model.pvalues.to_dict(),
            "r_squared": model.rsquared,
            "converged": True
        }
        
        logger.info(f"MLE Fallback successful. R-squared: {results['r_squared']:.4f}")
        return results
        
    except Exception as e:
        logger.error(f"MLE Fallback failed: {str(e)}")
        return {
            "method": "MLE_OLS",
            "status": "failed",
            "error": str(e),
            "converged": False
        }

def run_bayesian_model(
    df: pd.DataFrame,
    target_col: str,
    salience_col: str,
    foundation_cols: List[str],
    samples: int = 1000,
    tune: int = 1000,
    chains: int = 4,
    cores: int = 1,
    seed: Optional[int] = None
) -> Tuple[Optional[az.InferenceData], Dict[str, Any]]:
    """
    Execute the Bayesian model with robust convergence failure handling.
    
    Logic:
    1. Attempt MCMC sampling with PyMC.
    2. If sampling fails (exception) or diagnostics fail (R-hat > 1.05, divergences),
       log the failure, fallback to MLE, and flag the result as 'inconclusive' for Bayesian inference.
    3. If successful, return InferenceData and convergence stats.
    
    Args:
        df: Preprocessed dataframe containing variables.
        target_col: Name of the dependent variable (e.g., 'moral_judgment').
        salience_col: Name of the salience predictor (e.g., 'salience_level').
        foundation_cols: List of foundation scores to use as covariates.
        samples: Number of posterior samples.
        tune: Number of tuning steps.
        chains: Number of MCMC chains.
        cores: Number of CPU cores to use.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (InferenceData object or None, metadata_dict)
    """
    if seed is None:
        seed = int(np.random.randint(0, 10000))
        
    init_random_seeds(seed)
    log_pipeline_step("Bayesian Model Execution", "START", {"seed": seed})
    
    # Prepare data
    predictors = [salience_col] + foundation_cols
    clean_df = df.dropna(subset=[target_col] + predictors)
    
    if len(clean_df) == 0:
        log_exclusion("Bayesian Model", "No valid data after dropping NaNs", {"reason": "empty_dataset"})
        return None, {"status": "failed", "reason": "empty_dataset"}

    # Normalize predictors for better sampling (optional but recommended)
    # We store means and stds to interpret coefficients if needed later
    scaler_info = {}
    for col in predictors:
        scaler_info[col] = {
            "mean": clean_df[col].mean(),
            "std": clean_df[col].std()
        }
        # Standardize
        clean_df[f"{col}_std"] = (clean_df[col] - scaler_info[col]["mean"]) / (scaler_info[col]["std"] + 1e-8)
    
    # Build formula for PyMC (using standardised columns)
    # y ~ 1 + salience_std + foundation1_std + ... + interactions
    # Note: PyMC doesn't use formulas like statsmodels, so we construct matrices manually
    
    X = clean_df[[f"{c}_std" for c in predictors]].values
    y = clean_df[target_col].values.values
    
    n_predictors = X.shape[1]
    
    # Define Model
    with pm.Model() as model:
        # Priors
        sigma = pm.HalfNormal("sigma", 1.0)
        beta = pm.Normal("beta", mu=0, sigma=1, shape=n_predictors)
        intercept = pm.Normal("intercept", mu=0, sigma=1)
        
        # Likelihood
        mu = intercept + pm.math.dot(X, beta)
        y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)
        
        # Sampling
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trace = pm.sample(
                    draws=samples,
                    tune=tune,
                    chains=chains,
                    cores=cores,
                    random_seed=seed,
                    return_inferencedata=True,
                    progressbar=False
                )
            
            # Convergence Diagnostics
            r_hat = az.rhat(trace)
            n_divergences = trace.sample_stats.diverging.sum().values if hasattr(trace.sample_stats, 'diverging') else 0
            
            # Check R-hat for all parameters
            max_r_hat = max(r_hat.values.flatten())
            
            diagnostics = {
                "r_hat_max": float(max_r_hat),
                "n_divergences": int(n_divergences),
                "effective_samples": int(trace.posterior.effective_sample_size().mean())
            }
            
            # Determine Convergence
            is_converged = (max_r_hat < 1.05) and (n_divergences == 0)
            
            if not is_converged:
                log_exclusion(
                    "Bayesian Model", 
                    "Convergence diagnostics failed", 
                    {"r_hat": max_r_hat, "divergences": n_divergences}
                )
                logger.warning(f"Model did not converge (R-hat={max_r_hat:.3f}, Divergences={n_divergences}). Fallback to MLE.")
                
                # Fallback to MLE
                mle_results = _calculate_mle_estimates(
                    df, target_col, predictors, foundation_cols, salience_col
                )
                
                return None, {
                    "status": "inconclusive",
                    "reason": "convergence_failure",
                    "diagnostics": diagnostics,
                    "fallback_results": mle_results,
                    "original_seed": seed
                }
            
            log_pipeline_step("Bayesian Model Execution", "SUCCESS", {"r_hat": max_r_hat})
            return trace, {
                "status": "success",
                "diagnostics": diagnostics,
                "original_seed": seed
            }
            
        except Exception as e:
            # Catch any sampling errors (e.g., divergences that aren't caught by stats, initialization errors)
            log_exclusion("Bayesian Model", "Sampling exception", {"error": str(e)})
            logger.error(f"Bayesian sampling failed with exception: {str(e)}")
            
            # Fallback to MLE
            mle_results = _calculate_mle_estimates(
                df, target_col, predictors, foundation_cols, salience_col
            )
            
            return None, {
                "status": "inconclusive",
                "reason": "sampling_exception",
                "error": str(e),
                "fallback_results": mle_results,
                "original_seed": seed
            }

def main():
    """
    Main entry point for T023: Run Bayesian model with convergence handling.
    Loads processed data, runs the model, and saves results/metadata.
    """
    root = get_project_root()
    data_path = root / "data" / "processed" / "merged_dataset.csv"
    output_dir = root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not data_path.exists():
        logger.error(f"Input data not found at {data_path}. Run preprocessing first.")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Define columns based on schema (assumed from T016/T022)
    target = "moral_judgment"
    salience = "salience_level"
    # Assuming foundation columns are named like 'harm', 'fairness', etc.
    # We filter columns that are not ID, text, or metadata
    all_cols = df.columns.tolist()
    foundation_candidates = [c for c in all_cols if c not in [target, salience, 'id', 'story_text', 'participant_id']]
    
    # If specific foundation names are known, use them. Otherwise, use all numeric candidates.
    # For this implementation, we assume the first few numeric columns are foundations if specific names aren't found.
    # In a real scenario, this should be config-driven.
    foundations = foundation_candidates[:5] # Limit to top 5 for demo if too many
    
    if not foundations:
        logger.error("No foundation columns found in dataset.")
        sys.exit(1)
        
    logger.info(f"Running model with target={target}, salience={salience}, foundations={foundations}")
    
    trace, metadata = run_bayesian_model(
        df=df,
        target_col=target,
        salience_col=salience,
        foundation_cols=foundations,
        samples=500, # Reduced for speed in CI
        tune=500,
        chains=2,
        cores=1
    )
    
    # Save metadata
    import json
    metadata_path = output_dir / "bayesian_model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    # Save trace if successful
    if trace is not None:
        trace_path = output_dir / "bayesian_trace.nc"
        trace.to_netcdf(str(trace_path))
        logger.info(f"Trace saved to {trace_path}")
    else:
        logger.info("No trace saved (model was inconclusive or failed).")
        
    # Print summary to stdout for CI visibility
    print(json.dumps(metadata, indent=2, default=str))
    
    # Exit with non-zero if status is 'failed' (though 'inconclusive' is valid for T023 logic)
    if metadata["status"] == "failed":
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()