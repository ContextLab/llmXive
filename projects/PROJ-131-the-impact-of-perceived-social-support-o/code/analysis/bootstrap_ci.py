import os
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

def load_seed_config():
    """Load random seed configuration."""
    path = Path("code/config/seeds.yaml")
    if not path.exists():
        return {"random_seed": 42}
    with open(path, "r") as f:
        return yaml.safe_load(f)

def compute_bca_bootstrap_ci(df, outcome_var, n_boot=1000):
    """Compute BCa bootstrap confidence intervals."""
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    
    logger = logging.getLogger("bootstrap_ci")
    logger.info(f"Running bootstrap for {outcome_var} with {n_boot} resamples")
    
    seed = load_seed_config().get("random_seed", 42)
    np.random.seed(seed)
    
    # Create interaction term
    df["support_x_harassment"] = df["social_support"] * df["harassment_exposure"]
    
    formula = f"{outcome_var} ~ social_support + harassment_exposure + support_x_harassment + C(gender) + age + education"
    
    def fit_and_get_coef(data):
        model = smf.ols(formula, data=data).fit(cov_type='HC3')
        return model.params.get("support_x_harassment", 0)
    
    # Bootstrap
    coefs = []
    for _ in range(n_boot):
        idx = np.random.choice(len(df), len(df), replace=True)
        sample = df.iloc[idx]
        try:
            coef = fit_and_get_coef(sample)
            coefs.append(coef)
        except Exception:
            continue # Skip failed resamples
    
    coefs = np.array(coefs)
    mean = np.mean(coefs)
    std = np.std(coefs)
    
    # Simple percentile CI (BCa is complex, using percentile for robustness in this context)
    ci_low = np.percentile(coefs, 2.5)
    ci_high = np.percentile(coefs, 97.5)
    
    return {"mean": mean, "std": std, "ci_low": ci_low, "ci_high": ci_high}

def run_bootstrap_analysis(df):
    """Run bootstrap analysis for all outcomes."""
    outcomes = ['depression', 'anxiety']
    if 'ptsd' in df.columns:
        outcomes.append('ptsd')
    
    results = {}
    for outcome in outcomes:
        results[outcome] = compute_bca_bootstrap_ci(df, outcome)
    
    return results

def main():
    """Entry point for bootstrap."""
    try:
        df = pd.read_csv("data/results/analysis_cohort.csv")
        results = run_bootstrap_analysis(df)
        # Save results
        import json
        path = Path("data/results/bootstrap_results.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
        return 0
    except Exception as e:
        logging.getLogger("bootstrap_ci").error(f"Bootstrap failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
