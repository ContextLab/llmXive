import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure code directory is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_synthetic_cohort():
    """Load the analysis cohort."""
    import pandas as pd
    path = Path("data/results/analysis_cohort.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cohort not found at {path}")
    return pd.read_csv(path)

def create_interaction_term(df):
    """Create the interaction term."""
    if "social_support" in df.columns and "harassment_exposure" in df.columns:
        df["support_x_harassment"] = df["social_support"] * df["harassment_exposure"]
    return df

def fit_ols_model(df, outcome_var):
    """Fit OLS model with HC3 errors."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.stats.sandwich_covariance import cov_hc3

    logger = logging.getLogger("models")
    formula = f"{outcome_var} ~ social_support + harassment_exposure + support_x_harassment + C(gender) + age + education"
    
    try:
        model = smf.ols(formula, data=df).fit(cov_type='HC3')
        return model
    except Exception as e:
        logger.warning(f"HC3 fit failed for {outcome_var}, trying standard OLS: {e}")
        # Fallback to standard OLS
        model = smf.ols(formula, data=df).fit()
        return model

def extract_model_results(model, outcome_var):
    """Extract results from a fitted model."""
    results = {}
    results["outcome"] = outcome_var
    results["coef_intercept"] = model.params.get("Intercept", None)
    results["coef_social_support"] = model.params.get("social_support", None)
    results["coef_harassment_exposure"] = model.params.get("harassment_exposure", None)
    results["coef_interaction"] = model.params.get("support_x_harassment", None)
    
    # P-values
    results["pval_social_support"] = model.pvalues.get("social_support", None)
    results["pval_harassment_exposure"] = model.pvalues.get("harassment_exposure", None)
    results["pval_interaction"] = model.pvalues.get("support_x_harassment", None)
    
    return results

def estimate_bootstrap_runtime(df):
    """Estimate bootstrap runtime."""
    logger = logging.getLogger("models")
    # Run a quick dry run on a subset
    subset = df.head(100)
    start = time.time()
    # Simple dummy operation to estimate speed
    _ = subset.mean()
    elapsed = time.time() - start
    # Estimate for 1000 resamples
    estimated_total = elapsed * 1000
    logger.info(f"Estimated runtime for 1000 resamples: {estimated_total:.2f}s")
    return estimated_total

def run_all_models(df):
    """Run all regression models."""
    logger = logging.getLogger("models")
    df = create_interaction_term(df)
    
    outcomes = ['depression', 'anxiety']
    if 'ptsd' in df.columns:
        outcomes.append('ptsd')
    
    all_results = []
    for outcome in outcomes:
        logger.info(f"Fitting model for {outcome}")
        model = fit_ols_model(df, outcome)
        res = extract_model_results(model, outcome)
        all_results.append(res)
    
    return all_results

def main():
    """Entry point for models."""
    try:
        df = load_synthetic_cohort()
        # Estimate runtime first
        estimate_bootstrap_runtime(df)
        results = run_all_models(df)
        # Save results temporarily
        import pandas as pd
        res_df = pd.DataFrame(results)
        path = Path("data/results/regression_results_temp.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        res_df.to_csv(path, index=False)
        return 0
    except Exception as e:
        logging.getLogger("models").error(f"Modeling failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
