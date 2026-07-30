"""
Sensitivity Analysis Module for Social Support Resilience Study.

Implements robustness checks including continuous harassment definitions
and platform stratification with rigorous edge case handling.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import logger from project root
from logger import get_logger

logger = get_logger(__name__)

# Constants
MIN_STRATUM_SIZE = 30
MIN_VARIANCE_SD = 0.5

def load_synthetic_cohort() -> pd.DataFrame:
    """
    Load the analysis cohort from the validated CSV.
    Note: Despite the function name, this loads the single-dataset cohort
    as per the Revised Approach (Plan).
    """
    path = Path("data/results/analysis_cohort.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cohort file not found: {path}. Run preprocessing first.")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded analysis cohort with {len(df)} rows and {len(df.columns)} columns.")
    return df

def load_baseline_results() -> pd.DataFrame:
    """
    Load baseline regression results for comparison.
    """
    path = Path("data/results/regression_results.csv")
    if not path.exists():
        raise FileNotFoundError(f"Baseline results not found: {path}. Run modeling first.")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded baseline results with {len(df)} rows.")
    return df

def fit_ols_model_continuous(df: pd.DataFrame, outcome: str) -> Optional[Dict[str, Any]]:
    """
    Fit OLS model using continuous harassment severity instead of binary exposure.
    
    Args:
        df: DataFrame with continuous harassment severity
        outcome: Name of the outcome variable (e.g., 'depression')
        
    Returns:
        Dictionary with model results or None if fit fails
    """
    try:
        # Define predictors
        # Using continuous harassment severity
        predictors = ['social_support', 'harassment_severity', 
                     'social_support * harassment_severity',
                     'age', 'gender', 'education', 'income']
        
        # Create interaction term manually if not present
        if 'social_support * harassment_severity' not in df.columns:
            df['social_support * harassment_severity'] = df['social_support'] * df['harassment_severity']
        
        # Prepare design matrix
        # Note: statsmodels formula API is more robust for interaction terms
        formula = f"{outcome} ~ social_support + harassment_severity + social_support:harassment_severity + age + C(gender) + C(education) + income"
        
        model = sm.OLS.from_formula(formula, data=df)
        results = model.fit(cov_type='HC3')
        
        return {
            'coefficients': results.params.to_dict(),
            'std_errors': results.bse.to_dict(),
            'p_values': results.pvalues.to_dict(),
            'rsquared': results.rsquared,
            'n_obs': results.nobs
        }
    except Exception as e:
        logger.error(f"Failed to fit continuous model for {outcome}: {e}")
        return None

def stratify_by_platform(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Stratify the dataset by platform, rigorously handling low N edge cases.
    
    Per T046 requirements:
    - Groups with N < 30 are excluded and logged as E-SMALL-N-001
    - Groups with < 2 distinct categories (if applicable) are excluded
    - Does not arbitrarily truncate to "top three" platforms
    
    Args:
        df: Full analysis cohort
        
    Returns:
        Dictionary mapping valid platform names to their DataFrames
    """
    if 'platform' not in df.columns:
        logger.warning("No 'platform' column found in dataset. Skipping stratification.")
        return {}
    
    valid_strata = {}
    platform_counts = df['platform'].value_counts()
    
    logger.info(f"Found {len(platform_counts)} unique platforms in dataset.")
    
    for platform_name, count in platform_counts.items():
        # Edge Case 1: Low N
        if count < MIN_STRATUM_SIZE:
            logger.error(f"E-SMALL-N-001: Platform '{platform_name}' has N={count} < {MIN_STRATUM_SIZE}. Excluding from stratification.")
            continue
        
        # Edge Case 2: Variance check (if harassment_severity is the key variable)
        platform_df = df[df['platform'] == platform_name]
        if 'harassment_severity' in platform_df.columns:
            sd_val = platform_df['harassment_severity'].std()
            if pd.isna(sd_val) or sd_val < MIN_VARIANCE_SD:
                logger.error(f"E-LOW-VAR-001: Platform '{platform_name}' has SD={sd_val:.3f} < {MIN_VARIANCE_SD}. Excluding.")
                continue
        
        valid_strata[platform_name] = platform_df
        logger.info(f"Platform '{platform_name}' included with N={count}, SD={sd_val:.3f}")
    
    if len(valid_strata) < 2:
        logger.error("E-SKIP-001: Fewer than 2 valid platforms remain after filtering. Skipping stratification analysis.")
        return {}
    
    return valid_strata

def run_sensitivity_analysis(df: pd.DataFrame, outcomes: List[str] = None) -> List[Dict[str, Any]]:
    """
    Run full sensitivity analysis including continuous models and stratification.
    
    Args:
        df: Analysis cohort
        outcomes: List of outcome variables to test (default: depression, anxiety, ptsd)
        
    Returns:
        List of result dictionaries for each analysis
    """
    if outcomes is None:
        outcomes = ['depression', 'anxiety', 'ptsd']
    
    results = []
    
    # 1. Continuous Harassment Analysis (Global)
    logger.info("Running sensitivity analysis with continuous harassment severity...")
    for outcome in outcomes:
        if outcome not in df.columns:
            logger.warning(f"Outcome '{outcome}' not found in dataset. Skipping.")
            continue
        
        model_result = fit_ols_model_continuous(df, outcome)
        if model_result:
            results.append({
                'analysis_type': 'continuous_harassment_global',
                'outcome': outcome,
                'interaction_coef': model_result['coefficients'].get('social_support:harassment_severity', np.nan),
                'interaction_se': model_result['std_errors'].get('social_support:harassment_severity', np.nan),
                'interaction_p': model_result['p_values'].get('social_support:harashment_severity', np.nan),
                'n_obs': model_result['n_obs']
            })
    
    # 2. Platform Stratification
    logger.info("Running platform stratification analysis...")
    strata = stratify_by_platform(df)
    
    if not strata:
        logger.info("No valid strata for stratification analysis.")
        return results
    
    for platform_name, platform_df in strata.items():
        logger.info(f"Running stratified analysis for platform: {platform_name}")
        for outcome in outcomes:
            if outcome not in platform_df.columns:
                continue
            
            model_result = fit_ols_model_continuous(platform_df, outcome)
            if model_result:
                results.append({
                    'analysis_type': 'platform_stratified',
                    'platform': platform_name,
                    'outcome': outcome,
                    'interaction_coef': model_result['coefficients'].get('social_support:harassment_severity', np.nan),
                    'interaction_se': model_result['std_errors'].get('social_support:harassment_severity', np.nan),
                    'interaction_p': model_result['p_values'].get('social_support:harassment_severity', np.nan),
                    'n_obs': model_result['n_obs']
                })
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str = "data/results/sensitivity_analysis.csv"):
    """
    Save sensitivity analysis results to CSV.
    
    Args:
        results: List of result dictionaries
        output_path: Path for output file
    """
    if not results:
        logger.warning("No results to save.")
        return
    
    df_results = pd.DataFrame(results)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved sensitivity results to {output_path}")

def main():
    """
    Main entry point for sensitivity analysis execution.
    """
    logger.info("Starting Sensitivity Analysis (T046)...")
    
    try:
        # Load data
        df = load_synthetic_cohort()
        
        # Run analysis
        results = run_sensitivity_analysis(df)
        
        # Save results
        save_results(results)
        
        logger.info("Sensitivity Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
