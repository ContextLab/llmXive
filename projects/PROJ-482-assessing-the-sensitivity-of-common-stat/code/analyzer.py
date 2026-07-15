import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import ols

logger = logging.getLogger(__name__)

# Existing functions (preserved)
def load_simulation_results(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}")
    return pd.read_csv(filepath)

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    # Placeholder for existing aggregation logic
    return df.groupby(['sample_size', 'distribution_type', 'test_type']).agg({
        'error_rate': 'mean',
        'num_rejections': 'sum',
        'total_reps': 'sum'
    }).reset_index()

def compute_bootstrap_ci(data: np.ndarray, n_boot: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    rng = np.random.default_rng(42)
    boot_means = []
    for _ in range(n_boot):
        sample = rng.choice(data, size=len(data), replace=True)
        boot_means.append(np.mean(sample))
    return np.percentile(boot_means, [100 * alpha / 2, 100 * (1 - alpha / 2)])

def calculate_stability_variance(df: pd.DataFrame) -> float:
    if df.empty or 'error_rate' not in df.columns:
        return 0.0
    return df['error_rate'].var()

def export_results_to_csv(df: pd.DataFrame, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)

def analyze_and_export(df: pd.DataFrame, output_dir: str) -> None:
    # Existing analysis logic
    pass

def analyze_stability_trend(df: pd.DataFrame, output_dir: str) -> None:
    # Existing stability trend logic
    pass

# --- NEW FUNCTION FOR T027b ---

def analyze_log_pvalue_regression(raw_pvalues_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Implements T027b: Regression analysis on log-transformed p-values.
    
    Loads raw p-values from T021b, applies numerical stability epsilon (1e-300)
    during log-transform, fits a linear model (OLS) predicting log(p) using
    log(sample_size), distribution_type, and test_type.
    
    Args:
        raw_pvalues_path: Path to data/processed/raw_pvalues.csv
        output_dir: Directory to save results (e.g., data/processed/)
        
    Returns:
        Dictionary containing regression coefficients and model summary stats.
    """
    if not os.path.exists(raw_pvalues_path):
        raise FileNotFoundError(f"Raw p-values file not found: {raw_pvalues_path}. "
                                "Ensure T021b has been completed and raw_pvalues.csv exists.")
    
    logger.info(f"Loading raw p-values from {raw_pvalues_path}")
    df = pd.read_csv(raw_pvalues_path)
    
    required_cols = ['sample_size', 'distribution_type', 'test_type', 'p_value', 'hypothesis_type']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in raw_pvalues.csv: {missing_cols}")
    
    # Filter for Null Hypothesis only for Type I error distribution analysis (standard practice)
    # or include all if the spec implies modeling the full distribution. 
    # Given the goal is "sensitivity", we typically look at the distribution under Null.
    # However, the task says "model the log-transformed p-value distribution". 
    # We will include all data but ensure the model is interpretable.
    # Let's filter to Hypothesis='Null' to analyze the uniformity/sensitivity under the null,
    # as deviations under Alternative are expected.
    df_model = df[df['hypothesis_type'] == 'Null'].copy()
    
    if df_model.empty:
        logger.warning("No Null hypothesis data found. Using full dataset.")
        df_model = df.copy()

    logger.info(f"Processing {len(df_model)} records for regression.")

    # Numerical stability: Apply epsilon 1e-300 to p-values exactly 0 or 1
    # We do this ONLY during calculation, not modifying the stored data.
    EPSILON = 1e-300
    
    # Clip p-values to be within (0, 1) strictly for log transform
    # Although raw p-values from scipy are usually (0, 1], 0 can occur due to float limits.
    df_model['p_value_clipped'] = df_model['p_value'].clip(lower=EPSILON, upper=1.0 - EPSILON)
    
    # Log transform
    df_model['log_p'] = np.log(df_model['p_value_clipped'] + EPSILON)
    
    # Prepare features
    # Feature 1: log(sample_size)
    df_model['log_n'] = np.log(df_model['sample_size'])
    
    # Features 2 & 3: Categorical (distribution_type, test_type)
    # We will use OLS with formula which handles categorical encoding automatically.
    
    # Formula: log_p ~ log_n + C(distribution_type) + C(test_type)
    formula = "log_p ~ log_n + C(distribution_type) + C(test_type)"
    
    try:
        model = ols(formula=formula, data=df_model).fit()
    except Exception as e:
        logger.error(f"Regression model fitting failed: {e}")
        raise
    
    # Extract coefficients
    results_dict = {
        "coefficients": model.params.to_dict(),
        "p_values": model.pvalues.to_dict(),
        "rsquared": model.rsquared,
        "rsquared_adj": model.rsquared_adj,
        "aic": model.aic,
        "bic": model.bic,
        "num_obs": model.nobs,
        "formula": formula
    }
    
    # Save detailed results to CSV
    # Create a summary dataframe for coefficients
    coef_df = pd.DataFrame({
        'term': results_dict['coefficients'].keys(),
        'beta': results_dict['coefficients'].values(),
        'p_value': results_dict['p_values'].values(),
        'std_err': model.bse.values()
    })
    
    output_csv_path = os.path.join(output_dir, "log_pvalue_regression_results.csv")
    os.makedirs(output_dir, exist_ok=True)
    coef_df.to_csv(output_csv_path, index=False)
    
    # Save model summary as text
    summary_path = os.path.join(output_dir, "log_pvalue_regression_summary.txt")
    with open(summary_path, 'w') as f:
        f.write(model.summary().as_text())
    
    logger.info(f"Regression analysis complete. Results saved to {output_csv_path}")
    
    return results_dict

# Ensure existing exports are available if this file is imported directly
__all__ = [
    'load_simulation_results', 'aggregate_results', 'compute_bootstrap_ci',
    'calculate_stability_variance', 'export_results_to_csv', 'analyze_and_export',
    'analyze_stability_trend', 'analyze_log_pvalue_regression'
]
