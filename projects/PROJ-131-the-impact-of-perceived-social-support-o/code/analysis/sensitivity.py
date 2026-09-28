import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

def load_baseline_results():
    """Load baseline regression results."""
    path = Path("data/results/regression_results.csv")
    if not path.exists():
        raise FileNotFoundError(f"Baseline results not found at {path}")
    return pd.read_csv(path)

def fit_ols_model_continuous(df, outcome_var):
    """Fit model using continuous harassment severity."""
    import statsmodels.formula.api as smf
    formula = f"{outcome_var} ~ social_support + harassment_severity + social_support:harassment_severity + C(gender) + age + education"
    model = smf.ols(formula, data=df).fit()
    return model.params.get("social_support:harassment_severity", None)

def stratify_by_platform(df):
    """Stratify analysis by platform."""
    logger = logging.getLogger("sensitivity")
    if "platform" not in df.columns:
        logger.warning("W-NO-PLATFORM-001: Platform column missing. Skipping stratification.")
        return pd.DataFrame() # Return empty dataframe
    
    groups = df.groupby("platform")
    results = []
    valid_groups = 0
    
    for name, group in groups:
        if len(group) < 30:
            logger.warning(f"E-SMALL-N-001: Group {name} has N={len(group)} < 30. Skipping.")
            continue
        valid_groups += 1
        # Fit simple model for this group
        try:
            coef = fit_ols_model_continuous(group, "depression")
            results.append({"platform": name, "coef": coef, "n": len(group)})
        except Exception as e:
            logger.warning(f"Failed to fit model for {name}: {e}")
    
    if valid_groups == 1:
        logger.warning("W-STRAT-SINGLE-001: Only one valid platform group. Skipping stratification.")
        # Create header-only file
        path = Path("data/results/sensitivity_raw_stratified.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["platform", "coef", "n"]).to_csv(path, index=False)
        return pd.DataFrame()
    
    return pd.DataFrame(results)

def run_sensitivity_analysis(df):
    """Run sensitivity analyses."""
    logger = logging.getLogger("sensitivity")
    
    # 1. Continuous severity
    continuous_results = []
    for outcome in ['depression', 'anxiety']:
        if outcome in df.columns:
            coef = fit_ols_model_continuous(df, outcome)
            continuous_results.append({"outcome": outcome, "coef": coef, "type": "continuous"})
    
    cont_df = pd.DataFrame(continuous_results)
    
    # 2. Stratified
    strat_df = stratify_by_platform(df)
    
    return cont_df, strat_df

def save_results(cont_df, strat_df):
    """Save sensitivity results."""
    path_cont = Path("data/results/sensitivity_raw_continuous.csv")
    path_cont.parent.mkdir(parents=True, exist_ok=True)
    cont_df.to_csv(path_cont, index=False)
    
    path_strat = Path("data/results/sensitivity_raw_stratified.csv")
    if not strat_df.empty:
        strat_df.to_csv(path_strat, index=False)
    else:
        # Ensure header exists if empty
        pd.DataFrame(columns=["platform", "coef", "n"]).to_csv(path_strat, index=False)

def main():
    """Entry point for sensitivity analysis."""
    try:
        df = pd.read_csv("data/results/analysis_cohort.csv")
        cont_df, strat_df = run_sensitivity_analysis(df)
        save_results(cont_df, strat_df)
        return 0
    except Exception as e:
        logging.getLogger("sensitivity").error(f"Sensitivity analysis failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
