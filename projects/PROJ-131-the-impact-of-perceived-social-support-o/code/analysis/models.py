import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.config_loader import get_seed, load_yaml_config

def load_synthetic_cohort(file_path: Path, logger: logging.Logger):
    """Load the analysis cohort (single dataset approach)."""
    import pandas as pd
    logger.info(f"Loading analysis cohort from {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"Cohort file not found: {file_path}")
    return pd.read_csv(file_path)

def create_interaction_term(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Create interaction term: SocialSupport * HarassmentExposure."""
    logger.info("Creating interaction term.")
    df = df.copy()
    if 'social_support' in df.columns and 'harassment_exposure' in df.columns:
        df['interaction'] = df['social_support'] * df['harassment_exposure']
    else:
        logger.error("Missing columns for interaction term.")
        raise ValueError("Missing social_support or harassment_exposure.")
    return df

def fit_ols_model(df: pd.DataFrame, outcome: str, logger: logging.Logger):
    """Fit OLS model with HC3 standard errors."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    
    if outcome not in df.columns:
        logger.warning(f"Outcome {outcome} not in dataset. Skipping.")
        return None
    
    # Prepare formula
    covariates = ['age', 'gender', 'education', 'income']
    covariates = [c for c in covariates if c in df.columns]
    cov_str = " + ".join(covariates) if covariates else ""
    
    formula = f"{outcome} ~ social_support + harassment_exposure + interaction"
    if cov_str:
        formula += f" + {cov_str}"
    
    logger.info(f"Fitting model: {formula}")
    
    try:
        model = smf.ols(formula, data=df).fit()
        
        # HC3 SEs
        results = model.get_robustcov_results(cov_type='HC3')
        
        return {
            "model": results,
            "formula": formula,
            "outcome": outcome
        }
    except Exception as e:
        logger.error(f"Model fitting failed for {outcome}: {str(e)}")
        # Fallback to standard OLS
        logger.info("Falling back to standard OLS.")
        model = smf.ols(formula, data=df).fit()
        return {
            "model": model,
            "formula": formula,
            "outcome": outcome,
            "fallback": True
        }

def extract_model_results(model_info: Dict[str, Any]) -> Dict[str, Any]:
    """Extract coefficients, SEs, p-values from model results."""
    results = model_info["model"]
    outcome = model_info["outcome"]
    
    coef_df = results.summary2().tables[1]
    # Convert to dict for easier processing
    # Simplified extraction for the interaction term
    interaction_row = coef_df.loc['interaction']
    
    return {
        "outcome": outcome,
        "interaction_coef": interaction_row['Coef.'],
        "interaction_se": interaction_row['Std.Err'],
        "interaction_p": interaction_row['P>|t|'],
        "formula": model_info["formula"],
        "fallback": model_info.get("fallback", False)
    }

def estimate_bootstrap_runtime(df: pd.DataFrame, n_resamples: int, logger: logging.Logger) -> float:
    """Estimate bootstrap runtime using a small subset."""
    import time
    
    # Use a small subset for estimation
    subset = df.head(100)
    
    start = time.time()
    # Simulate one resample (simplified)
    _ = subset.sample(frac=1, replace=True, random_state=42)
    end = time.time()
    
    time_per_resample = end - start
    total_estimated = time_per_resample * n_resamples
    
    logger.info(f"Estimated time per resample: {time_per_resample:.4f}s")
    logger.info(f"Estimated total time for {n_resamples} resamples: {total_estimated:.2f}s ({total_estimated/3600:.2f} hours)")
    
    return total_estimated

def run_all_models(df: pd.DataFrame, outcomes: List[str], logger: logging.Logger) -> List[Dict[str, Any]]:
    """Run models for all outcomes."""
    df = create_interaction_term(df, logger)
    results = []
    
    for outcome in outcomes:
        if outcome not in df.columns:
            logger.warning(f"Skipping {outcome}: not in dataset.")
            continue
        
        model_info = fit_ols_model(df, outcome, logger)
        if model_info:
            res = extract_model_results(model_info)
            results.append(res)
    
    return results

def main():
    """Entry point for modeling (T020, T021, T024)."""
    logger = get_logger(__name__)
    logger.info("Starting Model Fitting")
    
    # Load cohort
    cohort_path = project_root / "data" / "results" / "analysis_cohort.csv"
    df = load_synthetic_cohort(cohort_path, logger)
    
    # Check bootstrap feasibility
    config = load_yaml_config(project_root / "code" / "config" / "bootstrap_config.yaml")
    n_resamples = config.get("n_resamples", 1000)
    
    est_time = estimate_bootstrap_runtime(df, n_resamples, logger)
    if est_time > 6 * 3600:
        logger.error("E-COMPUTE-OVERFLOW-001: Estimated runtime exceeds 6 hours. Halting.")
        raise RuntimeError("Bootstrap runtime overflow.")
    
    # Define outcomes
    outcomes = ['depression', 'anxiety']
    if 'ptsd' in df.columns:
        outcomes.append('ptsd')
    
    # Run models
    results = run_all_models(df, outcomes, logger)
    
    # Save results
    output_path = project_root / "data" / "results" / "regression_results.csv"
    import pandas as pd
    df_res = pd.DataFrame(results)
    df_res.to_csv(output_path, index=False)
    
    logger.info(f"Regression results saved to {output_path}")
    return results

if __name__ == "__main__":
    main()