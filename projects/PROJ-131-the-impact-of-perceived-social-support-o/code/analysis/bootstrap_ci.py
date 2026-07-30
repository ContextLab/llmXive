import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.bootstrap import BCaBootstrapResults
from statsmodels.regression.linear_model import OLS

# Configure logger
logger = logging.getLogger(__name__)

def load_seed_config(seed_path: Optional[str] = None) -> int:
    """
    Load the random seed from config/seeds.yaml.
    Defaults to 'config/seeds.yaml' if no path is provided.
    """
    if seed_path is None:
        # Resolve relative to project root (assumed to be parent of 'code')
        seed_path = Path(__file__).parent.parent / "config" / "seeds.yaml"
    
    if not os.path.exists(seed_path):
        raise FileNotFoundError(f"Seed configuration file not found at {seed_path}")
    
    with open(seed_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'random_seed' not in config:
        raise ValueError("Config file must contain 'random_seed' key")
    
    return int(config['random_seed'])

def compute_bca_bootstrap_ci(
    df: pd.DataFrame,
    formula: str,
    outcome_col: str,
    predictor_col: str,
    interaction_col: str,
    n_resamples: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute Bias-Corrected and Accelerated (BCa) bootstrap confidence intervals
    for the interaction term in an OLS regression.
    
    Args:
        df: The analysis dataframe.
        formula: The statsmodels formula string (e.g., "depression ~ social_support * harassment_severity + age + gender").
        outcome_col: Name of the dependent variable.
        predictor_col: Name of the main predictor (social support).
        interaction_col: Name of the interaction term column.
        n_resamples: Number of bootstrap resamples (default 1000 for stable estimation).
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary containing:
            - 'coef': Original coefficient estimate for the interaction term.
            - 'se': Standard error of the coefficient.
            - 'pvalue': P-value from the original OLS fit.
            - 'ci_lower': Lower bound of the BCa 95% CI.
            - 'ci_upper': Upper bound of the BCa 95% CI.
            - 'n_resamples': Number of resamples performed.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Prepare design matrix and outcome
    # Using statsmodels formula API for robust handling of categorical variables if needed
    try:
        model = sm.OLS.from_formula(formula, data=df)
        results = model.fit()
    except Exception as e:
        logger.error(f"Failed to fit initial OLS model for {outcome_col}: {e}")
        raise
    
    # Extract the index of the interaction term in the params array
    param_names = results.params.index.tolist()
    if interaction_col not in param_names:
        # Try to find a column that matches the pattern if exact match fails
        matching = [p for p in param_names if interaction_col in p]
        if not matching:
            raise ValueError(f"Interaction term '{interaction_col}' not found in model parameters. Available: {param_names}")
        interaction_idx = param_names.index(matching[0])
        logger.warning(f"Using matched parameter name '{matching[0]}' for interaction term.")
    else:
        interaction_idx = param_names.index(interaction_col)
    
    original_coef = results.params[interaction_idx]
    original_se = results.bse[interaction_idx]
    original_pvalue = results.pvalues[interaction_idx]
    
    # Define the statistic function for bootstrap
    # We need to extract the specific coefficient for the interaction term
    def statistic(data, indices):
        # Resample the data
        d = data.iloc[indices]
        try:
            # Refit the model on the resample
            # Note: from_formula on a subset might need careful handling if factors change,
            # but for continuous/standard variables it works.
            # We use the same formula string.
            # To ensure consistency, we might need to ensure the design matrix is built identically.
            # A safer approach for statsmodels bootstrap is to use the design matrix directly
            # but from_formula is more robust to missing categories in subsets if handled by statsmodels.
            # However, for strict reproducibility of the coefficient index, we rely on the formula.
            # If the subset drops a category, the index might shift.
            # Given the task constraints, we assume the formula is stable or use a wrapper.
            
            # Fallback: Fit using the formula. If it fails due to missing levels, return NaN.
            res = sm.OLS.from_formula(formula, data=d).fit()
            # Return the coefficient at the specific position if names match, else by index
            # To be safe against index shifting due to dropped categories, we look up by name if possible,
            # but the bootstrap function expects a scalar return.
            # We will assume the parameter name remains stable or we map it.
            # A more robust way: return res.params[interaction_col] if exists, else NaN
            if interaction_col in res.params.index:
                return res.params[interaction_col]
            else:
                # Fallback if the interaction term name is constructed differently (e.g., C(var):C(var))
                # This is a risk in bootstrap if subsets drop levels.
                # For this implementation, we assume the formula generates a stable name.
                return np.nan
        except Exception:
            return np.nan

    # Perform BCa Bootstrap
    # statsmodels.stats.bootstrap requires a function that takes (data, indices)
    # and returns a scalar (or array of scalars).
    try:
        bca_results = BCaBootstrapResults(
            statistic, 
            data=df, 
            n_replications=n_resamples,
            seed=seed
        )
        bca_results.fit()
    except Exception as e:
        logger.error(f"BCa Bootstrap failed for {outcome_col}: {e}. Falling back to standard bootstrap or raising.")
        raise

    # Extract CI
    # bca_results.conf_int returns a 2D array (lower, upper) for the parameter(s)
    # Since our statistic returns a scalar, we get one row.
    try:
        ci = bca_results.conf_int(alpha=0.05)
        ci_lower = ci[0, 0]
        ci_upper = ci[0, 1]
    except Exception as e:
        logger.warning(f"Could not extract BCa CI for {outcome_col}: {e}. Using percentile approximation.")
        # Fallback to percentile if BCa fails (rare)
        boot_vals = bca_results.bootstrap_stats
        ci_lower = np.percentile(boot_vals, 2.5)
        ci_upper = np.percentile(boot_vals, 97.5)

    return {
        'coef': float(original_coef),
        'se': float(original_se),
        'pvalue': float(original_pvalue),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'n_resamples': n_resamples
    }

def run_bootstrap_analysis(
    df: pd.DataFrame,
    formulas: Dict[str, str],
    interaction_col: str,
    n_resamples: int = 1000,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Run BCa bootstrap analysis for multiple outcomes.
    
    Args:
        df: Analysis dataframe.
        formulas: Dict mapping outcome name to statsmodels formula.
        interaction_col: Name of the interaction term.
        n_resamples: Number of resamples.
        seed: Random seed.
    
    Returns:
        DataFrame with bootstrap results for each outcome.
    """
    results = []
    
    for outcome_name, formula in formulas.items():
        logger.info(f"Running bootstrap for {outcome_name} (n={n_resamples})...")
        try:
            # Determine predictor and interaction names from formula if needed, 
            # but we assume the caller provides the correct interaction_col string.
            # We need to infer the main predictor name if not provided, but the task
            # implies we know the interaction term is "SocialSupport:HarassmentExposure".
            # We will assume the formula contains the interaction term as specified.
            # For the function, we pass the formula and let the extraction logic handle it.
            
            res = compute_bca_bootstrap_ci(
                df=df,
                formula=formula,
                outcome_col=outcome_name,
                predictor_col="social_support", # Assumed based on task context
                interaction_col=interaction_col,
                n_resamples=n_resamples,
                seed=seed
            )
            res['outcome'] = outcome_name
            results.append(res)
        except Exception as e:
            logger.error(f"Bootstrap analysis failed for {outcome_name}: {e}")
            # Append a row with NaNs to maintain schema
            results.append({
                'outcome': outcome_name,
                'coef': np.nan,
                'se': np.nan,
                'pvalue': np.nan,
                'ci_lower': np.nan,
                'ci_upper': np.nan,
                'n_resamples': n_resamples
            })
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for T021: Compute BCa Bootstrap CIs.
    This script is intended to be called by the pipeline or run standalone for testing.
    It expects the analysis cohort to exist at data/results/analysis_cohort.csv
    and outputs to data/results/bootstrap_ci_results.csv
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    project_root = Path(__file__).parent.parent
    cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"
    output_path = project_root / "data" / "results" / "bootstrap_ci_results.csv"
    seed_path = project_root / "config" / "seeds.yaml"
    
    if not cohort_path.exists():
        logger.error(f"Analysis cohort not found at {cohort_path}. Please run T016 first.")
        return
    
    logger.info(f"Loading analysis cohort from {cohort_path}")
    df = pd.read_csv(cohort_path)
    
    # Load seed
    seed = load_seed_config(str(seed_path))
    logger.info(f"Using random seed: {seed}")
    
    # Define formulas for Depression, Anxiety, PTSD
    # Assuming column names in the cohort match the spec:
    # depression, anxiety, ptsd, social_support, harassment_severity, age, gender, education, income
    # Interaction term is created in models.py or assumed to be present.
    # If the interaction term is not a column, we must construct it or use the formula string.
    # The task says "Include interaction term SocialSupport:HarassmentExposure".
    # In statsmodels formula, we write "social_support * harassment_severity" to generate main effects + interaction.
    # The interaction term name will be "social_support:harassment_severity".
    
    interaction_name = "social_support:harassment_severity"
    
    formulas = {
        'depression': 'depression ~ social_support * harassment_severity + age + gender + education + income',
        'anxiety': 'anxiety ~ social_support * harassment_severity + age + gender + education + income',
        'ptsd': 'ptsd ~ social_support * harassment_severity + age + gender + education + income'
    }
    
    # Check if PTSD column exists
    if 'ptsd' not in df.columns:
        logger.warning("PCL-5 (ptsd) column missing. Skipping PTSD model.")
        del formulas['ptsd']
    
    logger.info(f"Running bootstrap analysis with {len(formulas)} models...")
    results_df = run_bootstrap_analysis(
        df=df,
        formulas=formulas,
        interaction_col=interaction_name,
        n_resamples=1000,
        seed=seed
    )
    
    logger.info(f"Saving results to {output_path}")
    results_df.to_csv(output_path, index=False)
    logger.info("Bootstrap CI computation complete.")

if __name__ == "__main__":
    main()
