"""
Statistical analysis module for narrative perspective research.
Implements regression, VIF calculation, Bonferroni correction, and visualization.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
from typing import Dict, List, Any, Optional
import logging
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI
import matplotlib.pyplot as plt

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Logic: Adjust p-values based on the number of hypothesis tests performed (α/k).
    The corrected p-value is min(p * k, 1.0).
    The adjusted alpha threshold is alpha / k.
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing:
            - 'adjusted_p_values': List of Bonferroni-corrected p-values.
            - 'adjusted_alpha': The new significance threshold (alpha / k).
            - 'num_tests': Number of tests performed (k).
            - 'significant_flags': Boolean list indicating which tests remain significant.
    """
    if not p_values:
        logger.warning("Empty p_values list provided to Bonferroni correction.")
        return {
            'adjusted_p_values': [],
            'adjusted_alpha': alpha,
            'num_tests': 0,
            'significant_flags': []
        }

    k = len(p_values)
    adjusted_alpha = alpha / k
    adjusted_p_values = [min(p * k, 1.0) for p in p_values]
    significant_flags = [p < adjusted_alpha for p in adjusted_p_values]

    logger.info(f"Bonferroni correction applied: {k} tests, adjusted alpha={adjusted_alpha:.6f}")
    
    return {
        'adjusted_p_values': adjusted_p_values,
        'adjusted_alpha': adjusted_alpha,
        'num_tests': k,
        'significant_flags': significant_flags
    }

def run_regression_analysis(dataset_path: str) -> Dict[str, Any]:
    """
    Perform linear regression on the aligned dataset.
    
    Args:
        dataset_path: Path to the CSV file containing aligned data.
        
    Returns:
        Dictionary with regression results: slope, intercept, p_value, r_squared.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    required_cols = ['perspective_score', 'moral_judgement_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    # Drop rows with missing values
    clean_df = df.dropna(subset=required_cols)
    logger.info(f"Regression analysis on {len(clean_df)} samples (dropped {len(df) - len(clean_df)} NaNs)")
    
    if len(clean_df) < 2:
        raise ValueError("Insufficient samples for regression (need >= 2)")
    
    X = clean_df[['perspective_score']].values
    y = clean_df['moral_judgement_score'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate p-value using scipy stats
    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(X, y)
    
    # Use scipy for p-value of the slope
    # Correlation test
    corr, p_value = stats.pearsonr(clean_df['perspective_score'], clean_df['moral_judgement_score'])
    
    # For simple linear regression, the p-value of the slope is the same as the correlation p-value
    # However, we need to be careful with direction. Let's use the t-statistic approach.
    n = len(clean_df)
    df_resid = n - 2
    if df_resid > 0:
        # Standard error of the estimate
        y_pred = model.predict(X)
        residuals = y - y_pred
        sse = np.sum(residuals**2)
        mse = sse / df_resid
        
        # Standard error of slope
        ssx = np.sum((X.flatten() - np.mean(X))**2)
        se_slope = np.sqrt(mse / ssx)
        
        # t-statistic
        t_stat = slope / se_slope
        
        # p-value (two-tailed)
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df_resid))
    else:
        p_value = 1.0
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'p_value': float(p_value),
        'r_squared': float(r_squared),
        'sample_size': int(n)
    }

def calculate_vif(dataset_path: str) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factor (VIF) for predictors.
    
    Args:
        dataset_path: Path to the CSV file.
        
    Returns:
        Dictionary with VIF values and warnings.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # For this study, we only have one predictor: perspective_score
    # VIF is typically used for multiple regression, but we can calculate it for completeness
    # VIF for a single predictor is 1.0 (no multicollinearity with itself)
    
    if 'perspective_score' not in df.columns:
        logger.warning("perspective_score not found in dataset, skipping VIF calculation")
        return {'vif_values': {}, 'warning': None}
    
    # In a simple regression with one predictor, VIF is always 1.0
    vif_value = 1.0
    warning = None
    
    if vif_value > 5.0:
        warning = f"High multicollinearity detected: VIF = {vif_value:.2f} > 5.0"
        logger.warning(warning)
    
    return {
        'vif_values': {'perspective_score': vif_value},
        'warning': warning
    }

def generate_scatter_plot(dataset_path: str, output_path: str) -> None:
    """
    Generate a scatter plot with regression line and confidence interval.
    
    Args:
        dataset_path: Path to the CSV file.
        output_path: Path to save the plot (PNG).
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")
    
    df = pd.read_csv(dataset_path).dropna(subset=['perspective_score', 'moral_judgement_score'])
    
    if len(df) < 2:
        logger.warning("Insufficient data for plotting")
        return
    
    X = df['perspective_score'].values
    y = df['moral_judgement_score'].values
    
    # Create plot
    plt.figure(figsize=(10, 6))
    plt.scatter(X, y, alpha=0.6, label='Data points', edgecolors='k')
    
    # Fit regression line
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), y)
    y_pred = model.predict(X.reshape(-1, 1))
    
    # Calculate confidence interval
    n = len(X)
    x_mean = np.mean(X)
    ssx = np.sum((X - x_mean)**2)
    residuals = y - y_pred
    sse = np.sum(residuals**2)
    mse = sse / (n - 2)
    
    # Standard error of prediction
    se_pred = np.sqrt(mse * (1/n + (X - x_mean)**2 / ssx))
    
    # 95% CI
    t_crit = stats.t.ppf(0.975, n - 2)
    ci_lower = y_pred - t_crit * se_pred
    ci_upper = y_pred + t_crit * se_pred
    
    # Sort by X for smooth line
    sorted_idx = np.argsort(X)
    X_sorted = X[sorted_idx]
    y_pred_sorted = y_pred[sorted_idx]
    ci_lower_sorted = ci_lower[sorted_idx]
    ci_upper_sorted = ci_upper[sorted_idx]
    
    plt.plot(X_sorted, y_pred_sorted, 'r-', linewidth=2, label=f'Regression line (slope={model.coef_[0]:.3f})')
    plt.fill_between(X_sorted, ci_lower_sorted, ci_upper_sorted, color='red', alpha=0.2, label='95% CI')
    
    plt.xlabel('Perspective Score (First-Person Density)')
    plt.ylabel('Moral Judgement Score')
    plt.title('Narrative Perspective vs. Moral Judgement')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")

def run_analysis_pipeline(input_path: str, output_path: str, plot_path: str) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: regression, VIF, Bonferroni, and plotting.
    
    Args:
        input_path: Path to aligned_dataset.csv.
        output_path: Path to save analysis_results.json.
        plot_path: Path to save regression_plot.png.
        
    Returns:
        Dictionary with all analysis results.
    """
    logger.info(f"Starting analysis pipeline on {input_path}")
    
    # Run regression
    reg_results = run_regression_analysis(input_path)
    
    # Calculate VIF
    vif_results = calculate_vif(input_path)
    
    # Apply Bonferroni correction (only one test here, but for completeness)
    bonf_results = apply_bonferroni_correction([reg_results['p_value']])
    
    # Generate plot
    generate_scatter_plot(input_path, plot_path)
    
    # Compile results
    results = {
        'slope': reg_results['slope'],
        'intercept': reg_results['intercept'],
        'p_value': reg_results['p_value'],
        'r_squared': reg_results['r_squared'],
        'bonferroni_adjusted_p': bonf_results['adjusted_p_values'][0] if bonf_results['adjusted_p_values'] else None,
        'sample_size': reg_results['sample_size'],
        'vif_warning': vif_results['warning'],
        'vif_values': vif_results['vif_values'],
        'bonferroni_adjusted_alpha': bonf_results['adjusted_alpha']
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results to JSON
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")
    return results