import os
import sys
import logging
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import scipy.stats as stats
from statsmodels.stats.diagnostic import het_breuschpagan
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

from config import get_path, set_random_seed, BOOTSTRAP_ITERATIONS, RANDOM_SEED

# Configure logging
logger = logging.getLogger(__name__)

def load_daily_aggregates() -> pd.DataFrame:
    """Load the daily aggregates CSV file."""
    path = get_path('data/processed/daily_aggregates.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Daily aggregates file not found at {path}. Run preprocess.py first.")
    return pd.read_csv(path)

def load_model_results() -> Dict[str, Any]:
    """Load model results from JSON file if it exists."""
    path = get_path('data/processed/model_results.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_model_results(results: Dict[str, Any]) -> None:
    """Save model results to JSON file."""
    path = get_path('data/processed/model_results.json')
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {path}")

def validate_raw_mood_std(df: pd.DataFrame) -> bool:
    """
    Validate that the mood_std column contains no negative values or NaNs.
    Returns True if valid, False otherwise.
    """
    if 'mood_std' not in df.columns:
        logger.error("Column 'mood_std' not found in dataframe.")
        return False
    
    if df['mood_std'].isna().any():
        logger.error("mood_std contains NaN values.")
        return False
    
    if (df['mood_std'] < 0).any():
        logger.error("mood_std contains negative values.")
        return False
    
    logger.info("mood_std validation passed.")
    return True

def apply_log_transform(mood_std: np.ndarray) -> np.ndarray:
    """
    Apply log transform to mood_std with epsilon offset.
    This is the SINGLE authorized mechanism for log transformation.
    """
    epsilon = 1e-8
    return np.log(mood_std + epsilon)

def fit_lmm_variability(df: pd.DataFrame) -> Optional[Any]:
    """
    Fit Linear Mixed Model with log-transformed mood_std as outcome.
    Outcome: log(mood_std + epsilon)
    Predictor: total_steps
    Random effects: random intercepts for participant_id
    """
    if not validate_raw_mood_std(df):
        return None
    
    # Prepare data
    df = df.copy()
    df['log_mood_std'] = apply_log_transform(df['mood_std'].values)
    
    # Handle missing values in predictor
    df = df.dropna(subset=['total_steps', 'log_mood_std', 'participant_id'])
    
    if df.empty:
        logger.error("No valid data remaining for LMM variability model.")
        return None
    
    # Formula: log_mood_std ~ total_steps + sleep_duration + C(day_of_week) + baseline_affect
    # We need to handle potential NaNs in covariates
    formula = "log_mood_std ~ total_steps"
    
    # Add covariates if they exist and are not all NaN
    covariates = ['sleep_duration', 'baseline_affect']
    for cov in covariates:
        if cov in df.columns and df[cov].notna().any():
            formula += f" + {cov}"
    
    if 'day_of_week' in df.columns:
        formula += " + C(day_of_week)"
    
    try:
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        if not result.converged:
            logger.warning("LMM variability model did not converge.")
        
        return result
    except Exception as e:
        logger.error(f"Failed to fit LMM variability model: {e}")
        return None

def fit_lmm_mean(df: pd.DataFrame) -> Optional[Any]:
    """
    Fit Linear Mixed Model with mean_mood as outcome.
    Outcome: mean_mood
    Predictor: total_steps
    Random effects: random intercepts for participant_id
    """
    # Prepare data
    df = df.copy()
    df = df.dropna(subset=['total_steps', 'mean_mood', 'participant_id'])
    
    if df.empty:
        logger.error("No valid data remaining for LMM mean model.")
        return None
    
    formula = "mean_mood ~ total_steps"
    
    # Add covariates if they exist and are not all NaN
    covariates = ['sleep_duration', 'baseline_affect']
    for cov in covariates:
        if cov in df.columns and df[cov].notna().any():
            formula += f" + {cov}"
    
    if 'day_of_week' in df.columns:
        formula += " + C(day_of_week)"
    
    try:
        model = mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit()
        
        if not result.converged:
            logger.warning("LMM mean model did not converge.")
        
        return result
    except Exception as e:
        logger.error(f"Failed to fit LMM mean model: {e}")
        return None

def extract_model_coefficients(result: Any, model_name: str) -> Dict[str, Any]:
    """
    Extract fixed-effect coefficients, standard errors, p-values, and 95% CIs.
    """
    if result is None:
        return {}
    
    fixed_effects = {}
    params = result.params
    bse = result.bse
    
    for name, param in params.items():
        if name.startswith('participant'):
            continue
        
        t_stat = param / bse[name]
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), result.df_resid))
        
        # 95% CI
        ci_lower = param - 1.96 * bse[name]
        ci_upper = param + 1.96 * bse[name]
        
        fixed_effects[name] = {
            'estimate': float(param),
            'std_err': float(bse[name]),
            'p_value': float(p_value),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper)
        }
    
    random_effects = {}
    if hasattr(result, 'scale'):
        random_effects['residual_variance'] = float(result.scale)
    
    if hasattr(result, 'cov_re'):
        # Extract random intercept variance
        try:
            # The random effects covariance matrix is in result.cov_re
            # For a random intercept model, the diagonal element is the variance
            if isinstance(result.cov_re, pd.DataFrame):
                variances = np.diag(result.cov_re.values)
            else:
                variances = np.diag(result.cov_re)
            random_effects['participant_intercept_variance'] = float(variances[0]) if len(variances) > 0 else 0.0
        except:
            pass
    
    model_fit = {
        'aic': float(result.aic),
        'bic': float(result.bic),
        'log_likelihood': float(result.llf)
    }
    
    return {
        'model_type': model_name,
        'fixed_effects': fixed_effects,
        'random_effects': random_effects,
        'model_fit': model_fit
    }

def run_model_diagnostics(df: pd.DataFrame, model_result: Any) -> Dict[str, float]:
    """
    Perform model diagnostics: Shapiro-Wilk test on residuals and Breusch-Pagan test for heteroscedasticity.
    Also generates residual plots.
    
    Returns a dictionary with:
    - shapiro_wilk_p_value: p-value from Shapiro-Wilk test
    - breusch_pagan_p_value: p-value from Breusch-Pagan test
    """
    if model_result is None:
        logger.warning("No model result provided for diagnostics.")
        return {
            'shapiro_wilk_p_value': np.nan,
            'breusch_pagan_p_value': np.nan
        }
    
    # Get residuals and fitted values
    residuals = model_result.resid
    fitted = model_result.fittedvalues
    
    # Ensure we have valid data for tests
    valid_mask = ~np.isnan(residuals) & ~np.isnan(fitted)
    residuals = residuals[valid_mask]
    fitted = fitted[valid_mask]
    
    if len(residuals) < 3:
        logger.warning("Not enough data points for diagnostics.")
        return {
            'shapiro_wilk_p_value': np.nan,
            'breusch_pagan_p_value': np.nan
        }
    
    # 1. Shapiro-Wilk test for normality of residuals
    try:
        shapiro_stat, shapiro_p = stats.shapiro(residuals)
        shapiro_wilk_p_value = float(shapiro_p)
        logger.info(f"Shapiro-Wilk test: statistic={shapiro_stat:.4f}, p-value={shapiro_wilk_p_value:.4f}")
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}")
        shapiro_wilk_p_value = float('nan')
    
    # 2. Breusch-Pagan test for heteroscedasticity
    # We need to regress squared residuals on fitted values
    try:
        # Prepare data for Breusch-Pagan
        # The test requires exog (independent variables) - we use fitted values
        exog = sm.add_constant(fitted)
        endog = residuals ** 2
        
        # Fit OLS on squared residuals
        ols_model = sm.OLS(endog, exog).fit()
        bp_test = het_breuschpagan(ols_model.resid, ols_model.model.exog)
        
        # bp_test returns (lm_stat, lm_pvalue, f_stat, f_pvalue)
        breusch_pagan_p_value = float(bp_test[1])
        logger.info(f"Breusch-Pagan test: p-value={breusch_pagan_p_value:.4f}")
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {e}")
        breusch_pagan_p_value = float('nan')
    
    # 3. Generate residual plots
    try:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot 1: Residuals vs Fitted
        axes[0].scatter(fitted, residuals, alpha=0.5)
        axes[0].axhline(0, color='red', linestyle='--')
        axes[0].set_xlabel('Fitted Values')
        axes[0].set_ylabel('Residuals')
        axes[0].set_title('Residuals vs Fitted')
        axes[0].grid(True, alpha=0.3)
        
        # Add a smoothed line to check for patterns
        if len(fitted) > 10:
            # Sort by fitted values for smooth line
            sorted_idx = np.argsort(fitted)
            sorted_fitted = fitted[sorted_idx]
            sorted_residuals = residuals[sorted_idx]
            
            # Simple moving average
            window = min(10, len(sorted_fitted) // 5)
            if window > 1:
                smoothed = pd.Series(sorted_residuals).rolling(window=window, center=True, min_periods=1).mean()
                axes[0].plot(sorted_fitted, smoothed, color='blue', linewidth=2, label='Smoothed trend')
                axes[0].legend()
        
        # Plot 2: Q-Q plot
        sm.qqplot(residuals, line='45', fit=True, ax=axes[1])
        axes[1].set_title('Q-Q Plot of Residuals')
        
        plt.tight_layout()
        
        # Save the plot
        plot_path = get_path('data/processed', 'residual_plots.png')
        fig.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Residual plots saved to {plot_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate residual plots: {e}")
    
    return {
        'shapiro_wilk_p_value': shapiro_wilk_p_value,
        'breusch_pagan_p_value': breusch_pagan_p_value
    }

def run_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: fit models, extract coefficients, run diagnostics.
    Returns a dictionary containing all results.
    """
    set_random_seed(RANDOM_SEED)
    
    # Fit models
    logger.info("Fitting LMM for mood variability...")
    lmm_var_result = fit_lmm_variability(df)
    
    logger.info("Fitting LMM for mean mood...")
    lmm_mean_result = fit_lmm_mean(df)
    
    # Extract coefficients
    lmm_var_coeffs = extract_model_coefficients(lmm_var_result, "LMM_mood_variability")
    lmm_mean_coeffs = extract_model_coefficients(lmm_mean_result, "LMM_mean_mood")
    
    # Run diagnostics on the primary model (variability)
    logger.info("Running model diagnostics...")
    diagnostics = run_model_diagnostics(df, lmm_var_result)
    
    # Combine results
    results = {
        'variability_model': lmm_var_coeffs,
        'mean_model': lmm_mean_coeffs,
        'diagnostic_tests': diagnostics
    }
    
    return results

def main():
    """Main entry point for analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting analysis pipeline")
    
    try:
        # Load data
        df = load_daily_aggregates()
        logger.info(f"Loaded {len(df)} rows from daily aggregates")
        
        # Run analysis
        results = run_analysis(df)
        
        # Save results
        save_model_results(results)
        
        logger.info("Analysis pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()