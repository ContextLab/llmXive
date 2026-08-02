"""
Analysis module for Physical Activity and Mood Variability study.

Implements linear mixed-effects models, diagnostics, LOPO cross-validation,
and sensitivity analyses as specified in the research plan.
"""
import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm
from statsmodels.stats.diagnostic import het_breuschpagan
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any, Optional
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import configuration
from config import get_path

# Suppress specific warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

def load_daily_aggregates() -> pd.DataFrame:
    """Load the preprocessed daily aggregates dataset."""
    path = get_path('data/processed/daily_aggregates.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Daily aggregates file not found at {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from daily aggregates")
    return df

def fit_mood_std_model(df: pd.DataFrame, formula: Optional[str] = None) -> Any:
    """
    Fit a linear mixed-effects model with log-transformed mood_std as outcome.
    
    Args:
        df: DataFrame with daily aggregates
        formula: Optional custom formula. Defaults to:
                log_mood_std ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect
    
    Returns:
        Fitted model results
    """
    if formula is None:
        formula = "log_mood_std ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect"
    
    # Ensure log_mood_std exists (it should be pre-transformed in the CSV)
    if 'log_mood_std' not in df.columns:
        # Fallback if not pre-transformed, though task T015b ensures it is
        logger.warning("log_mood_std column not found, computing from mood_std + 0.01")
        df['log_mood_std'] = np.log(df['mood_std'] + 0.01)
    
    try:
        model = mixedlm.from_formula(formula, groups="participant_id", data=df)
        result = model.fit(reml=False)
        return result
    except Exception as e:
        logger.error(f"Failed to fit mood_std model: {e}")
        raise

def fit_mean_mood_model(df: pd.DataFrame, formula: Optional[str] = None) -> Any:
    """
    Fit a linear mixed-effects model with mean_mood as outcome.
    
    Args:
        df: DataFrame with daily aggregates
        formula: Optional custom formula. Defaults to:
                mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect
    
    Returns:
        Fitted model results
    """
    if formula is None:
        formula = "mean_mood ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect"
    
    try:
        model = mixedlm.from_formula(formula, groups="participant_id", data=df)
        result = model.fit(reml=False)
        return result
    except Exception as e:
        logger.error(f"Failed to fit mean_mood model: {e}")
        raise

def extract_results(result: Any, model_type: str) -> Dict[str, Any]:
    """
    Extract fixed effects, standard errors, p-values, and CIs from a fitted model.
    
    Args:
        result: Fitted mixedlm result object
        model_type: Identifier for the model (e.g., 'mood_std', 'mean_mood')
    
    Returns:
        Dictionary containing model results
    """
    params = result.params
    stderr = result.bse
    pvalues = result.pvalues
    conf_int = result.conf_int()
    
    # Extract total_steps specific stats
    steps_idx = 'total_steps'
    if steps_idx not in params.index:
        raise ValueError(f"total_steps not found in model parameters for {model_type}")
    
    results_dict = {
        "model_type": model_type,
        "converged": result.converged,
        "fixed_effects": params.to_dict(),
        "standard_errors": stderr.to_dict(),
        "p_values": pvalues.to_dict(),
        "confidence_intervals": {
            col: [conf_int.iloc[i, 0], conf_int.iloc[i, 1]] 
            for i, col in enumerate(params.index)
        },
        "total_steps_effect": {
            "coefficient": float(params[steps_idx]),
            "std_error": float(stderr[steps_idx]),
            "p_value": float(pvalues[steps_idx]),
            "ci_95": [float(conf_int.iloc[params.index.get_loc(steps_idx), 0]),
                      float(conf_int.iloc[params.index.get_loc(steps_idx), 1])]
        }
    }
    return results_dict

def run_model_diagnostics(df: pd.DataFrame, result: Any, model_name: str) -> Dict[str, Any]:
    """
    Perform model diagnostics: Shapiro-Wilk for normality and Breusch-Pagan for heteroscedasticity.
    Generates residual plots.
    
    Args:
        df: Original dataframe used for fitting
        result: Fitted model result
        model_name: Name for the model in reports
    
    Returns:
        Dictionary with diagnostic test results
    """
    residuals = result.resid
    fitted = result.fittedvalues
    
    diagnostics = {
        "model_name": model_name,
        "shapiro_wilk": {},
        "breusch_pagan": {},
        "plots": {}
    }
    
    # Shapiro-Wilk test for normality of residuals
    try:
        stat, p_val = stats.shapiro(residuals)
        diagnostics["shapiro_wilk"] = {
            "statistic": float(stat),
            "p_value": float(p_val),
            "normal": p_val > 0.05
        }
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}")
        diagnostics["shapiro_wilk"] = {"error": str(e)}
    
    # Breusch-Pagan test for heteroscedasticity
    # Requires exog (independent variables)
    try:
        # We need the design matrix or at least the exog used
        # Simplified: use fitted values or total_steps as exog for BP test
        bp_stat, bp_p, bp_f, bp_fp = het_breuschpagan(residuals, result.model.exog)
        diagnostics["breusch_pagan"] = {
            "statistic": float(bp_stat),
            "p_value": float(bp_p),
            "homoscedastic": bp_p > 0.05
        }
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {e}")
        diagnostics["breusch_pagan"] = {"error": str(e)}
    
    # Generate plots
    plt.figure(figsize=(10, 8))
    plt.scatter(fitted, residuals, alpha=0.6)
    plt.axhline(0, color='red', linestyle='--')
    plt.xlabel('Fitted Values')
    plt.ylabel('Residuals')
    plt.title(f'{model_name}: Residuals vs Fitted')
    
    plot_path = get_path(f'figures/{model_name}_residuals.png')
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path, dpi=150)
    plt.close()
    diagnostics["plots"]["residuals_vs_fitted"] = plot_path
    
    return diagnostics

def run_lopo_cross_validation(df: pd.DataFrame, n_splits: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform Leave-One-Participant-Out cross-validation.
    
    Args:
        df: Daily aggregates dataframe
        n_splits: Number of participants to leave out (defaults to unique participants)
    
    Returns:
        Dictionary with LOPO results including coefficient sign stability
    """
    participants = df['participant_id'].unique()
    if n_splits is None:
        n_splits = len(participants)
    
    logger.info(f"Starting LOPO CV with {n_splits} folds")
    
    coefficients = []
    signs = []
    
    for i, test_part in enumerate(participants[:n_splits]):
        train_df = df[df['participant_id'] != test_part]
        
        if len(train_df) < 10: # Safety check
            logger.warning(f"Fold {i} has too few samples, skipping")
            continue
        
        try:
            # Fit the primary model (mood_std)
            result = fit_mood_std_model(train_df)
            coef = result.params['total_steps']
            coefficients.append(coef)
            signs.append(1 if coef > 0 else -1)
            logger.info(f"Fold {i} (exclude {test_part}): coef={coef:.4f}, sign={signs[-1]}")
        except Exception as e:
            logger.error(f"Fold {i} failed: {e}")
            continue
    
    if not signs:
        return {"error": "No valid folds produced coefficients"}
    
    # Calculate sign stability
    # Compare each sign to the majority sign or the full-data sign
    # Here we compare to the median sign direction relative to the full model
    full_model = fit_mood_std_model(df)
    full_sign = 1 if full_model.params['total_steps'] > 0 else -1
    
    matches = sum(1 for s in signs if s == full_sign)
    stability_pct = (matches / len(signs)) * 100
    
    return {
        "n_folds": len(signs),
        "coefficients": coefficients,
        "signs": signs,
        "full_model_sign": full_sign,
        "matches": matches,
        "stability_percentage": stability_pct,
        "stable": stability_pct >= 90
    }

def run_sensitivity_analysis_active_minutes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Sensitivity analysis using 'active_minutes' instead of 'total_steps'.
    
    Args:
        df: Daily aggregates dataframe
    
    Returns:
        Dictionary with comparison results
    """
    if 'active_minutes' not in df.columns:
        logger.warning("active_minutes column not found, skipping this sensitivity analysis")
        return {"skipped": True, "reason": "active_minutes column missing"}
    
    # Fit model with active_minutes
    formula = "log_mood_std ~ active_minutes + sleep_duration + C(day_of_week) + baseline_affect"
    try:
        result = fit_mood_std_model(df, formula=formula)
        coef = result.params['active_minutes']
        p_val = result.pvalues['active_minutes']
        
        # Compare direction with standard model
        standard_result = fit_mood_std_model(df)
        standard_coef = standard_result.params['total_steps']
        
        direction_match = (coef > 0) == (standard_coef > 0)
        
        return {
            "metric": "active_minutes",
            "coefficient": float(coef),
            "p_value": float(p_val),
            "standard_model_coefficient": float(standard_coef),
            "direction_match": direction_match
        }
    except Exception as e:
        logger.error(f"Active minutes sensitivity analysis failed: {e}")
        return {"error": str(e)}

def run_sensitivity_analysis_exclude_single_ratings(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Sensitivity analysis excluding days with exactly one mood rating.
    
    Args:
        df: Daily aggregates dataframe (must have 'n_ratings' column)
    
    Returns:
        Dictionary with results of the model fitted on the filtered data
    """
    if 'n_ratings' not in df.columns:
        raise ValueError("Column 'n_ratings' not found in dataframe. Required for single-rating exclusion.")
    
    logger.info("Running sensitivity analysis: excluding single-rating days")
    
    # Filter out days with exactly 1 rating
    filtered_df = df[df['n_ratings'] != 1].copy()
    
    original_count = len(df)
    filtered_count = len(filtered_df)
    removed_count = original_count - filtered_count
    
    logger.info(f"Filtered dataset: {original_count} -> {filtered_count} rows (removed {removed_count} single-rating days)")
    
    if filtered_count < 10:
        raise ValueError("Filtered dataset too small for modeling after excluding single-rating days")
    
    # Fit the primary model on filtered data
    result = fit_mood_std_model(filtered_df)
    coef = result.params['total_steps']
    p_val = result.pvalues['total_steps']
    
    # Compare with full model
    full_result = fit_mood_std_model(df)
    full_coef = full_result.params['total_steps']
    
    direction_match = (coef > 0) == (full_coef > 0)
    
    return {
        "type": "exclude_single_ratings",
        "original_rows": original_count,
        "filtered_rows": filtered_count,
        "removed_rows": removed_count,
        "coefficient": float(coef),
        "p_value": float(p_val),
        "full_model_coefficient": float(full_coef),
        "direction_match": direction_match
    }

def run_sensitivity_analysis_impute_single_ratings(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Sensitivity analysis imputing single-rating days using participant median.
    
    Args:
        df: Daily aggregates dataframe
    
    Returns:
        Dictionary with results
    """
    if 'n_ratings' not in df.columns:
        raise ValueError("Column 'n_ratings' not found in dataframe.")
    
    logger.info("Running sensitivity analysis: imputing single-rating days")
    
    imputed_df = df.copy()
    
    # Identify single-rating rows
    single_rating_mask = imputed_df['n_ratings'] == 1
    
    if not single_rating_mask.any():
        logger.info("No single-rating days found to impute.")
        return {"skipped": True, "reason": "No single-rating days found"}
    
    # Impute mood_std with participant median (plus epsilon for log)
    # Note: We are imputing the outcome variable 'log_mood_std' or 'mood_std'?
    # The task implies we handle the data before modeling. 
    # If we have 'mood_std', we impute that. If we have 'log_mood_std', we impute that.
    # Assuming 'log_mood_std' is the outcome used in the model.
    
    target_col = 'log_mood_std'
    if target_col not in imputed_df.columns:
        # Fallback to mood_std if log_mood_std missing
        target_col = 'mood_std'
    
    # Calculate median per participant
    participant_medians = imputed_df.groupby('participant_id')[target_col].transform('median')
    
    # Impute
    imputed_df.loc[single_rating_mask, target_col] = participant_medians[single_rating_mask]
    
    logger.info(f"Imputed {single_rating_mask.sum()} single-rating days with participant medians")
    
    # Fit model
    result = fit_mood_std_model(imputed_df)
    coef = result.params['total_steps']
    p_val = result.pvalues['total_steps']
    
    # Compare with full model
    full_result = fit_mood_std_model(df)
    full_coef = full_result.params['total_steps']
    
    direction_match = (coef > 0) == (full_coef > 0)
    
    return {
        "type": "impute_single_ratings",
        "imputed_rows": int(single_rating_mask.sum()),
        "coefficient": float(coef),
        "p_value": float(p_val),
        "full_model_coefficient": float(full_coef),
        "direction_match": direction_match
    }

def run_analysis() -> Dict[str, Any]:
    """
    Run the full analysis pipeline including primary models, diagnostics, LOPO, and sensitivity analyses.
    
    Returns:
        Dictionary containing all analysis results
    """
    logger.info("Starting full analysis pipeline")
    
    # Load data
    df = load_daily_aggregates()
    
    # Primary Models
    logger.info("Fitting primary models...")
    mood_std_result = fit_mood_std_model(df)
    mean_mood_result = fit_mean_mood_model(df)
    
    results = {
        "mood_std_model": extract_results(mood_std_result, "mood_std"),
        "mean_mood_model": extract_results(mean_mood_result, "mean_mood"),
        "diagnostics": {},
        "lopo": {},
        "sensitivity": {}
    }
    
    # Diagnostics
    logger.info("Running diagnostics...")
    results["diagnostics"]["mood_std"] = run_model_diagnostics(df, mood_std_result, "mood_std")
    results["diagnostics"]["mean_mood"] = run_model_diagnostics(df, mean_mood_result, "mean_mood")
    
    # LOPO
    logger.info("Running LOPO cross-validation...")
    results["lopo"] = run_lopo_cross_validation(df)
    
    # Sensitivity Analysis: Active Minutes
    logger.info("Running active minutes sensitivity...")
    results["sensitivity"]["active_minutes"] = run_sensitivity_analysis_active_minutes(df)
    
    # Sensitivity Analysis: Exclude Single Ratings (T031a)
    logger.info("Running exclude single-rating sensitivity...")
    try:
        results["sensitivity"]["exclude_single_ratings"] = run_sensitivity_analysis_exclude_single_ratings(df)
    except Exception as e:
        logger.error(f"Exclude single-rating analysis failed: {e}")
        results["sensitivity"]["exclude_single_ratings"] = {"error": str(e)}
    
    # Sensitivity Analysis: Impute Single Ratings (T031b - preparing for T031c)
    logger.info("Running impute single-rating sensitivity...")
    try:
        results["sensitivity"]["impute_single_ratings"] = run_sensitivity_analysis_impute_single_ratings(df)
    except Exception as e:
        logger.error(f"Impute single-rating analysis failed: {e}")
        results["sensitivity"]["impute_single_ratings"] = {"error": str(e)}
    
    # Save results
    output_path = get_path('data/processed/model_results.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    return results

def main():
    """Entry point for the analysis script."""
    try:
        results = run_analysis()
        print("Analysis completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())