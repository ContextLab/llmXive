"""
Analysis module for User Story 2: Diversity Analysis and pH Correlation.

Implements Linear Mixed-Effects (LME) models to correlate diversity with pH.
Handles fallback logic for small datasets and non-linearity detection.
"""
import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# Import from project utilities and transformations
from utils import get_logger, setup_logging
from transformations import check_normality

# Ensure output directories exist
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_transformed_diversity_data(filepath: str = "data/processed/diversity_transformed.csv") -> pd.DataFrame:
    """
    Load the transformed diversity data from the previous step (T021).
    
    Args:
        filepath: Path to the transformed diversity CSV file.
        
    Returns:
        DataFrame containing diversity metrics and metadata.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}. Run T021 first.")
    
    df = pd.read_csv(filepath)
    required_cols = ['sample_id', 'pH', 'site', 'shannon_diversity', 'simpson_diversity']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {filepath}: {missing_cols}")
    
    return df

def run_lme_model(df: pd.DataFrame, 
                  diversity_col: str = 'shannon_diversity', 
                  predictor: str = 'pH', 
                  random_effect: str = 'site') -> Dict[str, Any]:
    """
    Run a Linear Mixed-Effects model: diversity ~ pH + (1|site).
    
    Uses statsmodels to fit the model. Handles cases where the random effect
    grouping has insufficient levels by falling back to fixed effects.
    
    Args:
        df: DataFrame with diversity and metadata.
        diversity_col: Column name for the diversity metric.
        predictor: Column name for the predictor variable (pH).
        random_effect: Column name for the random effect grouping (site).
        
    Returns:
        Dictionary containing model results: estimate, se, p_value, model_type.
    """
    logger = logging.getLogger(__name__)
    
    # Check for sufficient sites for random effect
    unique_sites = df[random_effect].nunique()
    model_type = "LME"
    
    formula = f"{diversity_col} ~ {predictor} + (1|{random_effect})"
    
    try:
        if unique_sites < 2:
            logger.warning(f"Only {unique_sites} site(s) found. Cannot fit random effect. Falling back to OLS.")
            model_type = "OLS"
            formula = f"{diversity_col} ~ {predictor}"
            model = smf.ols(formula, data=df)
            results = model.fit()
        else:
            # Try fitting LME (using MixedLM from statsmodels)
            # Note: statsmodels MixedLM syntax is slightly different from lme4 R syntax
            # We map (1|site) to groups=df[site]
            grouped_data = df.groupby(random_effect)
            if len(grouped_data) < 2:
                logger.warning(f"Only {len(grouped_data)} groups found. Falling back to OLS.")
                model_type = "OLS"
                formula = f"{diversity_col} ~ {predictor}"
                model = smf.ols(formula, data=df)
                results = model.fit()
            else:
                # Prepare data for MixedLM: need endog, exog, groups
                endog = df[diversity_col]
                exog = sm.add_constant(df[predictor])
                groups = df[random_effect]
                
                # Fit the model
                # Note: MixedLM doesn't support formula interface directly in older versions,
                # but we can construct it manually or use a helper if available.
                # Using the manual approach for robustness:
                model = sm.MixedLM(endog, exog, groups=groups)
                results = model.fit()
                
    except Exception as e:
        logger.error(f"Error fitting LME model: {e}")
        logger.warning("Falling back to OLS due to model fitting error.")
        model_type = "OLS"
        formula = f"{diversity_col} ~ {predictor}"
        model = smf.ols(formula, data=df)
        results = model.fit()
    
    # Extract coefficients
    # The coefficient for the predictor (pH) is at index 1 if 'const' is 0
    # In MixedLM, params includes 'group' variances, so we need to be careful.
    # In OLS, it's straightforward.
    
    if model_type == "OLS":
        # OLS results
        coef = results.params[predictor]
        se = results.bse[predictor]
        p_value = results.pvalues[predictor]
    else:
        # MixedLM results
        # Fixed effects are in results.fixed_effects or results.params
        # The index order depends on how exog was constructed.
        # Since we used sm.add_constant, index 0 is const, index 1 is predictor.
        fixed_effects = results.fixed_effects
        # Get the parameter for the predictor
        # The keys in fixed_effects are usually the column names if passed as DataFrame,
        # but here exog is ndarray. So we rely on position.
        # However, MixedLM results.params includes random effects variance.
        # Let's use the fixed_effects attribute which should map to exog columns if named.
        # If exog is ndarray, we assume order: const, predictor.
        # To be safe, let's check the shape and keys.
        if hasattr(results, 'fixed_effects'):
            fe = results.fixed_effects
            # If fe is a Series/DataFrame with names, use predictor name.
            if predictor in fe.index:
                coef = fe[predictor]
                se = results.bse[predictor] # This might not work directly for MixedLM
                # For MixedLM, standard errors are in results.cov_params() diagonal
                # But let's try to get the bse for the fixed effect.
                # A safer way:
                params = results.params
                # The fixed effects are the first len(exog[0]) parameters.
                # We need to map the predictor to its index.
                # Since exog was sm.add_constant(df[predictor]), index 1 is predictor.
                coef = params[1]
                # Get covariance matrix for fixed effects
                cov = results.cov_params()
                # The variance of the fixed effect at index 1
                se = np.sqrt(cov.iloc[1, 1])
                # P-value requires t-statistic
                t_stat = coef / se
                # Degrees of freedom for MixedLM is approximate, often n - k
                # statsmodels MixedLM doesn't give exact p-values easily without Satterthwaite approx
                # We'll use a large df approximation or the built-in if available.
                # For simplicity and robustness, we calculate p-value from t-stat using normal approx or t with df=n-k
                df_model = len(df) - len(exog[0])
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df_model))
            else:
                # Fallback if keys don't match
                coef = params[1]
                cov = results.cov_params()
                se = np.sqrt(cov.iloc[1, 1])
                t_stat = coef / se
                df_model = len(df) - len(exog[0])
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df_model))
        else:
            # Last resort
            coef = results.params[1]
            cov = results.cov_params()
            se = np.sqrt(cov.iloc[1, 1])
            t_stat = coef / se
            df_model = len(df) - 2
            p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df_model))

    return {
        "estimate": float(coef),
        "se": float(se),
        "p_value": float(p_value),
        "model_type": model_type,
        "r_squared": float(results.rsquared) if hasattr(results, 'rsquared') else None,
        "n_obs": len(df),
        "n_groups": unique_sites
    }

def detect_nonlinearity(df: pd.DataFrame, 
                        diversity_col: str = 'shannon_diversity', 
                        predictor: str = 'pH') -> Tuple[bool, float]:
    """
    Detect non-linearity in the relationship between diversity and pH.
    
    Compares a linear model to a quadratic model. If the quadratic term
    is significant, suggests non-linearity.
    
    Args:
        df: DataFrame with data.
        diversity_col: Diversity metric column.
        predictor: Predictor column.
        
    Returns:
        Tuple of (is_nonlinear, p_value_quadratic).
    """
    logger = logging.getLogger(__name__)
    
    # Create quadratic term
    df_temp = df.copy()
    df_temp[f"{predictor}_sq"] = df_temp[predictor] ** 2
    
    formula_linear = f"{diversity_col} ~ {predictor}"
    formula_quad = f"{diversity_col} ~ {predictor} + {predictor}_sq"
    
    model_linear = smf.ols(formula_linear, data=df_temp).fit()
    model_quad = smf.ols(formula_quad, data=df_temp).fit()
    
    # Check if quadratic term is significant
    p_val_quad = model_quad.pvalues[f"{predictor}_sq"]
    is_nonlinear = p_val_quad < 0.05
    
    if is_nonlinear:
        logger.warning(f"Non-linearity detected (p={p_val_quad:.4f}). Suggest adding polynomial term.")
        
    return is_nonlinear, p_val_quad

def run_analysis_pipeline(input_file: str = "data/processed/diversity_transformed.csv",
                          output_file: str = "data/processed/lme_results.csv") -> None:
    """
    Run the full analysis pipeline for T022a.
    
    1. Load transformed diversity data.
    2. Run LME model for Shannon diversity.
    3. Run LME model for Simpson diversity.
    4. Detect non-linearity.
    5. Save results to CSV.
    
    Args:
        input_file: Path to input transformed diversity CSV.
        output_file: Path to output results CSV.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting analysis pipeline. Input: {input_file}")
    
    try:
        df = load_transformed_diversity_data(input_file)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    results = []
    
    # Run LME for Shannon Diversity
    logger.info("Running LME for Shannon Diversity...")
    try:
        shannon_results = run_lme_model(df, diversity_col='shannon_diversity')
        shannon_results['metric'] = 'shannon_diversity'
        results.append(shannon_results)
    except Exception as e:
        logger.error(f"Error running Shannon LME: {e}")
        results.append({
            "metric": "shannon_diversity",
            "estimate": None,
            "se": None,
            "p_value": None,
            "model_type": "ERROR",
            "r_squared": None,
            "n_obs": len(df),
            "n_groups": df['site'].nunique()
        })
    
    # Run LME for Simpson Diversity
    logger.info("Running LME for Simpson Diversity...")
    try:
        simpson_results = run_lme_model(df, diversity_col='simpson_diversity')
        simpson_results['metric'] = 'simpson_diversity'
        results.append(simpson_results)
    except Exception as e:
        logger.error(f"Error running Simpson LME: {e}")
        results.append({
            "metric": "simpson_diversity",
            "estimate": None,
            "se": None,
            "p_value": None,
            "model_type": "ERROR",
            "r_squared": None,
            "n_obs": len(df),
            "n_groups": df['site'].nunique()
        })
    
    # Non-linearity check
    logger.info("Checking for non-linearity...")
    is_nonlinear, p_quad = detect_nonlinearity(df)
    with open(OUTPUT_DIR / "nonlinearity_check.json", "w") as f:
        json.dump({"is_nonlinear": is_nonlinear, "p_value_quadratic": p_quad}, f)
    
    # Convert results to DataFrame and save
    results_df = pd.DataFrame(results)
    # Reorder columns to match task requirement: estimate, se, p_value, model_type
    # Plus metric for clarity
    cols = ['metric', 'estimate', 'se', 'p_value', 'model_type', 'r_squared', 'n_obs', 'n_groups']
    results_df = results_df[[c for c in cols if c in results_df.columns]]
    
    results_df.to_csv(output_file, index=False)
    logger.info(f"Results saved to {output_file}")

def main():
    """Main entry point for the analysis script."""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Starting T022a: LME Analysis")
    
    try:
        run_analysis_pipeline()
        logger.info("T022a completed successfully.")
    except Exception as e:
        logger.error(f"T022a failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
