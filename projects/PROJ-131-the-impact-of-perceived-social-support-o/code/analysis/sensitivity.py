"""
Sensitivity Analysis Module.

Implements T027a (Continuous Severity), T027b (Platform Stratification), T029 (Save Summary).
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.cohort import RESULTS_DIR
from analysis.models import load_synthetic_cohort, create_interaction_term, fit_ols_model, extract_model_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_baseline_results():
    """Loads the baseline regression results."""
    path = RESULTS_DIR / "regression_results.csv"
    if not path.exists():
        raise FileNotFoundError(f"Baseline results not found: {path}")
    return pd.read_csv(path)

def fit_ols_model_continuous(df: pd.DataFrame, outcome: str) -> Optional[Dict[str, Any]]:
    """
    Fits OLS using continuous harassment severity instead of binary exposure.
    T027a Implementation.
    """
    try:
        import statsmodels.api as sm
        
        if outcome not in df.columns:
            return None

        # Formula: Y ~ SocialSupport + HarassmentSeverity (Continuous) + Interaction(Support * Severity) + Covariates
        covariates = ['age', 'gender', 'education', 'income']
        valid_covariates = [c for c in covariates if c in df.columns]
        
        formula = f"{outcome} ~ social_support + harassment_severity + social_support:harassment_severity"
        if valid_covariates:
            formula += " + " + " + ".join(valid_covariates)
        
        model = sm.formula.ols(formula, data=df)
        results = model.fit(cov_type='HC3')
        
        return extract_model_results(results, outcome)
    except Exception as e:
        logger.error(f"Continuous model failed for {outcome}: {e}")
        return None

def stratify_by_platform(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Stratifies analysis by platform.
    T027b Implementation.
    """
    # Check for platform column
    if 'platform' not in df.columns:
        logger.warning("W-NO-PLATFORM-001: 'platform' column not found. Skipping stratification.")
        return []
    
    platforms = df['platform'].dropna().unique()
    logger.info(f"Found platforms: {platforms}")
    
    results = []
    valid_platforms = []
    
    for plat in platforms:
        group = df[df['platform'] == plat]
        n = len(group)
        if n < 30:
            logger.warning(f"E-SMALL-N-001: Platform '{plat}' has N={n} (<30). Skipping.")
            continue
        
        valid_platforms.append(plat)
        logger.info(f"Running stratified model for {plat} (N={n})...")
        
        # Run models for this group
        group = create_interaction_term(group)
        for outcome in ['depression', 'anxiety', 'ptsd']:
            if outcome in group.columns:
                res = fit_ols_model(group, outcome)
                if res:
                    extracted = extract_model_results(res, outcome)
                    extracted['platform'] = str(plat)
                    results.append(extracted)
    
    if len(valid_platforms) == 1:
        logger.warning("W-STRAT-SINGLE-001: Only one valid platform group found. Skipping stratification.")
        return []
        
    return results

def run_sensitivity_analysis(df: pd.DataFrame):
    """
    Orchestrates sensitivity analysis.
    """
    logger.info("Running Sensitivity Analysis (T027)...")
    
    # 1. Continuous Severity (T027a)
    continuous_results = []
    df_cont = create_interaction_term(df) # Ensure interaction exists if needed
    # Note: For continuous, we might need to re-create interaction with severity
    # But the function fit_ols_model_continuous handles the formula directly.
    for outcome in ['depression', 'anxiety', 'ptsd']:
        if outcome in df.columns:
            res = fit_ols_model_continuous(df, outcome)
            if res:
                res['model_type'] = 'continuous_severity'
                continuous_results.append(res)
    
    # 2. Platform Stratification (T027b)
    stratified_results = stratify_by_platform(df)
    
    return continuous_results, stratified_results

def save_results(continuous_results: List[Dict], stratified_results: List[Dict]):
    """
    Saves sensitivity results to CSV.
    T029 Implementation.
    """
    # Flatten continuous
    cont_flat = []
    for r in continuous_results:
        for name, coef in r.get('coefficients', {}).items():
            cont_flat.append({
                "outcome": r.get('outcome'),
                "term": name,
                "coef": coef,
                "se": r.get('se', {}).get(name, 0),
                "p_value": r.get('p_values', {}).get(name, 1),
                "model_type": "continuous_severity",
                "platform": "ALL"
            })
    
    # Flatten stratified
    strat_flat = []
    for r in stratified_results:
        for name, coef in r.get('coefficients', {}).items():
            strat_flat.append({
                "outcome": r.get('outcome'),
                "term": name,
                "coef": coef,
                "se": r.get('se', {}).get(name, 0),
                "p_value": r.get('p_values', {}).get(name, 1),
                "model_type": "stratified",
                "platform": r.get('platform', 'UNKNOWN')
            })
    
    df_cont = pd.DataFrame(cont_flat)
    df_strat = pd.DataFrame(strat_flat)
    
    # Save separate files as per T027a/T027b deliverables
    if not df_cont.empty:
        df_cont.to_csv(RESULTS_DIR / "sensitivity_raw_continuous.csv", index=False)
        logger.info(f"Saved continuous results to {RESULTS_DIR / 'sensitivity_raw_continuous.csv'}")
    
    if not df_strat.empty:
        df_strat.to_csv(RESULTS_DIR / "sensitivity_raw_stratified.csv", index=False)
        logger.info(f"Saved stratified results to {RESULTS_DIR / 'sensitivity_raw_stratified.csv'}")
    else:
        logger.info("No stratified results to save.")
    
    # Combine for T029 summary
    all_sens = pd.concat([df_cont, df_strat], ignore_index=True)
    if not all_sens.empty:
        all_sens.to_csv(RESULTS_DIR / "sensitivity_analysis.csv", index=False)
        logger.info(f"Saved sensitivity summary to {RESULTS_DIR / 'sensitivity_analysis.csv'}")

def main():
    """Entry point for T027-T029."""
    logger.info("Starting Sensitivity Analysis...")
    try:
        df = load_synthetic_cohort()
        cont_res, strat_res = run_sensitivity_analysis(df)
        save_results(cont_res, strat_res)
        logger.info("Sensitivity Analysis completed.")
    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
