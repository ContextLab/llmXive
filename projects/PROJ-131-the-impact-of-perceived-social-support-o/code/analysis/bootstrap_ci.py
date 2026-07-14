import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.bootstrap import _bootstrap, BCaBootstrapResults

from analysis.models import run_all_models, load_synthetic_cohort
from logger import get_logger

logger = get_logger(__name__)

def load_seed_config() -> int:
    """
    Load the bootstrap seed from config/seeds.yaml.
    Returns an integer seed value.
    """
    config_path = Path("config/seeds.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Seed configuration file not found at {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    if "bootstrap_seed" not in config:
        raise ValueError("bootstrap_seed key missing in config/seeds.yaml")
    
    seed = config["bootstrap_seed"]
    logger.info(f"Loaded bootstrap seed: {seed}")
    return int(seed)

def compute_bca_bootstrap_ci(
    model_results: Dict[str, Any],
    data: pd.DataFrame,
    outcome: str,
    formula: str,
    n_resamples: int = 1000,
    seed: int = 42
) -> BCaBootstrapResults:
    """
    Compute Bias-Corrected and Accelerated (BCa) bootstrap confidence intervals
    for a specific OLS model outcome.

    Args:
        model_results: Dictionary containing pre-fitted model results (not strictly used by statsmodels bootstrap, 
                       but kept for context if needed).
        data: The synthetic cohort DataFrame.
        outcome: Name of the dependent variable column.
        formula: The regression formula string (e.g., "Depression ~ SocialSupport + HarassmentExposure + SocialSupport:HarassmentExposure").
        n_resamples: Number of bootstrap resamples (default 1000).
        seed: Random seed for reproducibility.

    Returns:
        BCaBootstrapResults object containing coefficients and confidence intervals.
    """
    logger.info(f"Computing BCa bootstrap CI for {outcome} with {n_resamples} resamples (seed={seed})")
    
    # Ensure reproducibility
    np.random.seed(seed)

    # Prepare data for statsmodels bootstrap
    # We need to pass the data and the model function
    def fit_model(data_subset: pd.DataFrame) -> sm.OLSResults:
        try:
            # Re-fit the model on the subset
            # Note: statsmodels formula API handles the parsing
            model = sm.OLS.from_formula(formula, data=data_subset)
            # Use HC3 robust standard errors as per T020 requirements
            results = model.fit(cov_type='HC3')
            return results
        except Exception as e:
            logger.warning(f"Model fitting failed on bootstrap sample: {e}")
            # Return None or a dummy result to handle failures gracefully?
            # statsmodels bootstrap expects a callable that returns an array-like or dict.
            # We will raise to let the bootstrap handle it if configured, 
            # but usually we want to skip bad samples. 
            # For now, we let it raise, assuming clean data.
            raise e

    # Use statsmodels' bootstrap utility
    # We extract the coefficients we care about.
    # The _bootstrap function in statsmodels.stats.bootstrap is low-level.
    # We use the higher level approach by defining a statistic function.
    
    def stat_func(data: pd.DataFrame) -> np.ndarray:
        res = fit_model(data)
        # Return coefficients as a 1D array
        return res.params.values

    try:
        # statsmodels.stats.bootstrap module has a helper for this
        # However, the direct API often requires a bit of setup.
        # Let's use the standard approach:
        # statsmodels.stats.bootstrap.bootstrap
        
        # We need to wrap the data in a way statsmodels expects or use the low level _bootstrap
        # A cleaner way with statsmodels is to use the Bootstrap class or similar, 
        # but the task specifically mentions `statsmodels.stats.bootstrap`.
        
        # Let's use the _bootstrap function directly which is the core engine.
        # It returns an array of shape (n_resamples, n_params)
        
        # Prepare the full dataset for the bootstrap engine
        # We pass the data and the statistic function
        
        # Note: statsmodels.stats.bootstrap._bootstrap signature:
        # _bootstrap(data, statistic, func_args=(), func_kwds=None, nrep=1000, 
        #            block_size=0, seed=None, use_pandas=False)
        
        # We need to ensure the data passed to _bootstrap is a numpy array or DataFrame 
        # that the statistic function can index.
        
        boot_results = _bootstrap(
            data=data,
            statistic=stat_func,
            nrep=n_resamples,
            seed=seed,
            use_pandas=True
        )
        
        # boot_results is an array of shape (n_resamples, n_params)
        # Now compute BCa intervals
        # statsmodels.stats.bootstrap has a function to compute BCa intervals from bootstrap distribution
        # However, the public API for BCa is often wrapped in a specific class or method.
        # Let's use the `statsmodels.stats.bootstrap` module's `BCa` class if available, 
        # or implement the calculation manually if the API is low-level.
        
        # Checking statsmodels version compatibility:
        # In recent versions, we can use `statsmodels.stats.bootstrap` utilities.
        # If `BCaBootstrapResults` is not directly instantiable from raw array easily without a specific class,
        # we calculate the intervals.
        
        # Let's use the `statsmodels.stats.bootstrap` `bootstrap` function if available, 
        # which returns a `BootstrapResults` object.
        # Actually, `statsmodels.stats.bootstrap` has a `bootstrap` function that returns a tuple 
        # (mean, std, conf_int) if using basic methods, but for BCa we need specific logic.
        
        # Alternative: Use the `statsmodels.stats.bootstrap` `BCa` class (if available in version)
        # or compute manually.
        # Given the constraint to use `statsmodels.stats.bootstrap`, and assuming a standard installation:
        # We will compute the BCa intervals manually from the `boot_results` array 
        # using standard formulas, as the high-level `BCa` class might not be directly 
        # exposed in all versions or requires a specific model wrapper.
        
        # Manual BCa calculation:
        # 1. Calculate bias correction (z0)
        # 2. Calculate acceleration (a)
        # 3. Calculate adjusted percentiles
        
        # 1. Bias Correction (z0)
        # Proportion of bootstrap estimates less than the original estimate
        original_estimate = stat_func(data) # Estimate from full data
        n_params = len(original_estimate)
        
        z0 = np.zeros(n_params)
        for i in range(n_params):
            prop_less = np.mean(boot_results[:, i] < original_estimate[i])
            # Avoid log(0) or log(1)
            prop_less = np.clip(prop_less, 1e-10, 1 - 1e-10)
            z0[i] = sm.stats.norm.ppf(prop_less)
        
        # 2. Acceleration (a)
        # Requires jackknife estimates
        jackknife_estimates = np.zeros((len(data), n_params))
        for i in range(len(data)):
            # Leave one out
            jack_data = data.drop(index=data.index[i])
            jackknife_estimates[i] = stat_func(jack_data)
        
        theta_jack = jackknife_estimates.mean(axis=0)
        numerator = np.sum((theta_jack - jackknife_estimates).mean(axis=0)**3)
        denominator = 6 * np.sum((theta_jack - jackknife_estimates).mean(axis=0)**2)**1.5
        
        if denominator == 0:
            a = 0
        else:
            a = numerator / denominator
        
        # 3. Calculate adjusted percentiles for 95% CI
        alpha = 0.05
        z_alpha = sm.stats.norm.ppf(alpha / 2)
        z_1_alpha = sm.stats.norm.ppf(1 - alpha / 2)
        
        # Adjusted percentiles
        # alpha_star = Phi(z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha)))
        
        alpha_star_low = sm.stats.norm.cdf(z0 + (z0 + z_alpha) / (1 - a * (z0 + z_alpha) + 1e-10))
        alpha_star_high = sm.stats.norm.cdf(z0 + (z0 + z_1_alpha) / (1 - a * (z0 + z_1_alpha) + 1e-10))
        
        # Clip percentiles to [0, 1]
        alpha_star_low = np.clip(alpha_star_low, 0, 1)
        alpha_star_high = np.clip(alpha_star_high, 0, 1)
        
        # Get quantiles from bootstrap distribution
        ci_low = np.percentile(boot_results, alpha_star_low * 100, axis=0)
        ci_high = np.percentile(boot_results, alpha_star_high * 100, axis=0)
        
        # Construct a simple result structure
        # We return a dictionary or a simple object that mimics BCaBootstrapResults
        # The task asks to "Compute" and likely save.
        # We will return a dict with params and CIs.
        
        results_dict = {
            "outcome": outcome,
            "params": original_estimate,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "alpha": alpha
        }
        
        logger.info(f"BCa Bootstrap CI computed for {outcome}")
        return results_dict

    except Exception as e:
        logger.error(f"BCa Bootstrap failed for {outcome}: {e}")
        raise

def run_bootstrap_analysis() -> List[Dict[str, Any]]:
    """
    Orchestrates the bootstrap analysis for all models defined in T020.
    """
    seed = load_seed_config()
    data = load_synthetic_cohort()
    
    # Define models based on T020 (Depression, Anxiety, PTSD)
    # Assuming column names match the spec
    outcomes = ["Depression", "Anxiety", "PTSD"]
    # Only run for outcomes present in data
    available_outcomes = [o for o in outcomes if o in data.columns]
    
    if not available_outcomes:
        logger.warning("No valid outcome variables found for bootstrap analysis.")
        return []
    
    base_formula = "{outcome} ~ SocialSupport + HarassmentExposure + SocialSupport:HarassmentExposure"
    
    all_results = []
    
    for outcome in available_outcomes:
        formula = base_formula.format(outcome=outcome)
        # Run the base model first to ensure it works (T020 logic)
        # We assume T020 has already run or we run it here for context
        # But for bootstrap, we just need the data and formula.
        
        # We need the original estimate for BCa calculation
        # We can get it by fitting once
        model = sm.OLS.from_formula(formula, data=data)
        original_results = model.fit(cov_type='HC3')
        original_params = original_results.params.values
        
        # Run bootstrap
        boot_result = compute_bca_bootstrap_ci(
            model_results={"params": original_params},
            data=data,
            outcome=outcome,
            formula=formula,
            n_resamples=1000,
            seed=seed
        )
        all_results.append(boot_result)
    
    return all_results

def main():
    """
    Entry point for T021: Compute BCa Bootstrap CIs.
    """
    try:
        results = run_bootstrap_analysis()
        
        if not results:
            logger.warning("No bootstrap results generated.")
            return
        
        # Convert results to a DataFrame for saving (T024 will likely read this)
        # We need to flatten the results for each parameter
        rows = []
        for res in results:
            outcome = res["outcome"]
            params = res["params"]
            ci_low = res["ci_low"]
            ci_high = res["ci_high"]
            # Assuming the order of params is consistent with the formula
            # We need the variable names.
            # We can get them from the original model fit or assume standard order.
            # Let's re-fit to get variable names
            formula = f"{outcome} ~ SocialSupport + HarassmentExposure + SocialSupport:HarassmentExposure"
            model = sm.OLS.from_formula(formula, data=load_synthetic_cohort())
            var_names = model.exog_names
            
            for i, var in enumerate(var_names):
                rows.append({
                    "outcome": outcome,
                    "variable": var,
                    "coef": params[i],
                    "ci_low": ci_low[i],
                    "ci_high": ci_high[i]
                })
        
        df_results = pd.DataFrame(rows)
        
        output_path = Path("data/results/bootstrap_ci_results.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(output_path, index=False)
        logger.info(f"Bootstrap CI results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
