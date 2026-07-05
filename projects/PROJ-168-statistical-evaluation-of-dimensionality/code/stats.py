"""
Statistical analysis module for dimensionality reduction evaluation.

Implements Mixed-Effects Model fitting (dataset as random intercept) with
fallback to Fixed-Effects ANOVA when dataset count is insufficient.
Includes Benjamini-Hochberg correction for multiple comparisons.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

# Import from sibling modules
from config import set_case_study_mode, get_accession_seed, Config
from utils import log_memory_usage

logger = logging.getLogger(__name__)

def load_aggregated_metrics(results_dir: Path) -> pd.DataFrame:
    """
    Load aggregated geometry and fidelity metrics from results directory.
    
    Args:
        results_dir: Path to the results directory containing aggregated data.
        
    Returns:
        DataFrame containing combined metrics for statistical modeling.
    """
    aggregated_file = results_dir / "aggregated_metrics.csv"
    if not aggregated_file.exists():
        raise FileNotFoundError(
            f"Aggregated metrics file not found: {aggregated_file}. "
            "Run code/aggregate.py first (T023.5)."
        )
    
    df = pd.read_csv(aggregated_file)
    logger.info(f"Loaded {len(df)} records from {aggregated_file}")
    return df

def check_collinearity(df: pd.DataFrame, formula: str) -> Tuple[bool, List[str]]:
    """
    Calculate Variance Inflation Factor (VIF) to check for collinearity.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string.
        
    Returns:
        Tuple of (is_collinear, list of predictors with VIF >= 5).
    """
    try:
        # Prepare design matrix
        y, X = dmatrices(formula, data=df, return_type='dataframe')
        # Add constant if not present
        if 'Intercept' not in X.columns:
            X = sm.add_constant(X)
        
        vif_data = []
        high_vif_predictors = []
        
        for i, col in enumerate(X.columns):
            if col == 'Intercept':
                continue
            # Calculate VIF for each predictor
            vif = sm.OLS(X[col], X.drop(columns=[col])).fit().rsquared
            # VIF = 1 / (1 - R^2)
            if vif >= 1.0:
                vif_val = 1.0 / (1.0 - vif)
            else:
                vif_val = np.inf
            
            vif_data.append((col, vif_val))
            if vif_val >= 5.0:
                high_vif_predictors.append(col)
        
        is_collinear = len(high_vif_predictors) > 0
        if is_collinear:
            logger.warning(f"Collinearity detected: VIF >= 5 for {high_vif_predictors}")
        
        return is_collinear, high_vif_predictors
        
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return False, []

def fit_mixed_effects_model(
    df: pd.DataFrame,
    formula: str = "fidelity ~ method + (1|dataset)",
    results_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Fit a Mixed-Effects Model with dataset as random intercept.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string.
        results_dir: Optional path to save results.
        
    Returns:
        Dictionary containing model results and statistics.
    """
    logger.info("Fitting Mixed-Effects Model...")
    
    # Check dataset count
    unique_datasets = df['dataset'].nunique()
    if unique_datasets < 2:
        logger.warning(f"Only {unique_datasets} dataset(s) found. "
                     "Mixed-Effects Model requires >= 2. Falling back to Fixed-Effects ANOVA.")
        set_case_study_mode(True)
        return fit_fixed_effects_anova(df, formula.replace("(1|dataset)", ""), results_dir)
    
    # Check collinearity
    is_collinear, high_vif = check_collinearity(df, formula)
    if is_collinear:
        logger.warning(f"High VIF detected for: {high_vif}. Proceeding with caution.")
    
    # Fit model using statsmodels (using Patsy for formula parsing)
    # Note: statsmodels doesn't natively support (1|dataset) syntax like lme4 in R.
    # We use MixedLM for this purpose.
    try:
        # Prepare data for MixedLM
        # Formula: fidelity ~ method
        # Random intercept: dataset
        
        # Convert categorical variables
        df['method'] = pd.Categorical(df['method'])
        df['dataset'] = pd.Categorical(df['dataset'])
        
        # Create design matrices
        y = df['fidelity'].values
        X = sm.model.api.dmatrix("method", data=df, return_type='dataframe')
        groups = df['dataset'].values
        
        # Add constant
        X = sm.add_constant(X)
        
        # Fit MixedLM
        model = sm.MixedLM(y, X, groups=groups, exog_re=np.ones((len(df), 1)))
        result = model.fit()
        
        logger.info(f"Model converged: {result.converged}")
        logger.info(f"Log-likelihood: {result.llf}")
        
        # Extract results
        fixed_effects = result.params
        p_values = result.pvalues
        aic = result.aic
        bic = result.bic
        
        # Apply Benjamini-Hochberg correction
        p_values_array = np.array([p_values.get(col, np.nan) for col in fixed_effects.index if col != 'const'])
        if len(p_values_array) > 0:
            corrected_p_values = multipletests(p_values_array, method='fdr_bh')[1]
            corrected_dict = {
                col: corrected_p_values[i] 
                for i, col in enumerate(fixed_effects.index) 
                if col != 'const' and col in p_values
            }
        else:
            corrected_dict = {}
        
        results = {
            "model_type": "Mixed-Effects",
            "formula": formula,
            "n_datasets": unique_datasets,
            "n_observations": len(df),
            "converged": bool(result.converged),
            "log_likelihood": float(result.llf) if not np.isinf(result.llf) else None,
            "aic": float(aic),
            "bic": float(bic),
            "fixed_effects": {k: float(v) for k, v in fixed_effects.items()},
            "p_values": {k: float(v) for k, v in p_values.items()},
            "corrected_p_values": corrected_dict,
            "random_effects_variance": float(result.scale) if hasattr(result, 'scale') else None,
            "high_vif_predictors": high_vif,
            "status": "success"
        }
        
        if results_dir:
            save_results(results, results_dir, "mixed_effects_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"Mixed-Effects Model fitting failed: {e}")
        logger.info("Attempting fallback to Fixed-Effects ANOVA...")
        set_case_study_mode(True)
        return fit_fixed_effects_anova(df, formula.replace("(1|dataset)", ""), results_dir, str(e))

def fit_fixed_effects_anova(
    df: pd.DataFrame,
    formula: str = "fidelity ~ method",
    results_dir: Optional[Path] = None,
    fallback_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects ANOVA model.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string.
        results_dir: Optional path to save results.
        fallback_reason: Reason for fallback (optional).
        
    Returns:
        Dictionary containing model results and statistics.
    """
    logger.info("Fitting Fixed-Effects ANOVA...")
    
    try:
        # Fit OLS model
        model = smf.ols(formula, data=df)
        result = model.fit()
        
        # Get ANOVA table
        anova_table = sm.stats.anova_lm(result, typ=2)
        
        # Extract p-values
        p_values = result.pvalues
        
        # Apply Benjamini-Hochberg correction
        p_values_array = np.array([p_values.get(col, np.nan) for col in p_values.index if col != 'Intercept'])
        if len(p_values_array) > 0:
            corrected_p_values = multipletests(p_values_array, method='fdr_bh')[1]
            corrected_dict = {
                col: corrected_p_values[i] 
                for i, col in enumerate(p_values.index) 
                if col != 'Intercept'
            }
        else:
            corrected_dict = {}
        
        # Extract F-statistics and p-values from ANOVA table
        anova_results = {}
        for row in anova_table.index:
            if row != 'Residual':
                anova_results[row] = {
                    "sum_sq": float(anova_table.loc[row, 'sum_sq']),
                    "df": float(anova_table.loc[row, 'df']),
                    "F": float(anova_table.loc[row, 'F']),
                    "PR(>F)": float(anova_table.loc[row, 'PR(>F)'])
                }
        
        results = {
            "model_type": "Fixed-Effects ANOVA",
            "formula": formula,
            "n_datasets": df['dataset'].nunique(),
            "n_observations": len(df),
            "fallback_reason": fallback_reason,
            "r_squared": float(result.rsquared),
            "adj_r_squared": float(result.rsquared_adj),
            "aic": float(result.aic),
            "bic": float(result.bic),
            "anova_table": anova_results,
            "p_values": {k: float(v) for k, v in p_values.items()},
            "corrected_p_values": corrected_dict,
            "status": "success"
        }
        
        if results_dir:
            save_results(results, results_dir, "anova_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"Fixed-Effects ANOVA fitting failed: {e}")
        return {
            "model_type": "Fixed-Effects ANOVA",
            "status": "failed",
            "error": str(e)
        }

def run_interaction_test(
    df: pd.DataFrame,
    results_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run ANOVA F-tests to evaluate interaction terms.
    
    Args:
        df: DataFrame containing the data.
        results_dir: Optional path to save results.
        
    Returns:
        Dictionary containing interaction test results.
    """
    logger.info("Running interaction tests...")
    
    # Check if we have enough data for interaction
    if df['dataset'].nunique() < 2:
        logger.warning("Insufficient datasets for interaction test.")
        return {"status": "skipped", "reason": "Insufficient datasets"}
    
    try:
        # Formula with interaction
        formula = "fidelity ~ method * dataset"
        model = smf.ols(formula, data=df)
        result = model.fit()
        
        # Get ANOVA table
        anova_table = sm.stats.anova_lm(result, typ=2)
        
        # Extract interaction term p-value
        interaction_results = {}
        for row in anova_table.index:
            if 'method:dataset' in row or 'dataset:method' in row:
                interaction_results[row] = {
                    "sum_sq": float(anova_table.loc[row, 'sum_sq']),
                    "df": float(anova_table.loc[row, 'df']),
                    "F": float(anova_table.loc[row, 'F']),
                    "PR(>F)": float(anova_table.loc[row, 'PR(>F)'])
                }
        
        # Apply Benjamini-Hochberg correction if multiple interactions
        if len(interaction_results) > 0:
            p_values = np.array([v['PR(>F)'] for v in interaction_results.values()])
            corrected = multipletests(p_values, method='fdr_bh')[1]
            for i, key in enumerate(interaction_results):
                interaction_results[key]['corrected_PR(>F)'] = float(corrected[i])
        
        results = {
            "formula": formula,
            "interaction_terms": interaction_results,
            "alpha": 0.05,
            "status": "success"
        }
        
        if results_dir:
            save_results(results, results_dir, "interaction_test_results.json")
        
        return results
        
    except Exception as e:
        logger.error(f"Interaction test failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }

def save_results(results: Dict[str, Any], results_dir: Path, filename: str) -> None:
    """Save results to JSON file."""
    results_dir.mkdir(parents=True, exist_ok=True)
    output_file = results_dir / filename
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to {output_file}")

def main():
    """Main entry point for statistical analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Get paths from config
    results_dir = Path(Config.RESULTS_DIR)
    data_dir = Path(Config.PROCESSED_DATA_DIR)
    
    try:
        # Load aggregated metrics
        df = load_aggregated_metrics(results_dir)
        
        # Run Mixed-Effects Model
        mixed_results = fit_mixed_effects_model(df, results_dir=results_dir)
        
        # Run interaction test
        interaction_results = run_interaction_test(df, results_dir=results_dir)
        
        # Summary
        summary = {
            "mixed_effects": mixed_results["status"],
            "interaction_test": interaction_results.get("status", "not_run"),
            "n_datasets": df['dataset'].nunique(),
            "n_observations": len(df)
        }
        
        save_results(summary, results_dir, "stats_summary.json")
        logger.info("Statistical analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
