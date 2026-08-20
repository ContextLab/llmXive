import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
from typing import Dict, List, Any, Optional
import logging
import json
import os
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

def run_regression_analysis(dataset_path: str) -> Dict[str, Any]:
    """
    Perform linear regression with perspective_score as predictor and moral_judgement_score as outcome.
    Returns slope, intercept, p_value, r_squared.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file {dataset_path} not found.")
    
    df = pd.read_csv(dataset_path)
    
    # Ensure required columns exist
    required_cols = ['perspective_score', 'moral_judgement_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop NaN values
    df = df.dropna(subset=required_cols)
    
    if len(df) < 2:
        logger.warning("Insufficient data points for regression.")
        return {
            'slope': None,
            'intercept': None,
            'p_value': None,
            'r_squared': None,
            'sample_size': len(df)
        }
    
    X = df['perspective_score'].values.reshape(-1, 1)
    y = df['moral_judgement_score'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    slope = model.coef_[0]
    intercept = model.intercept_
    r_squared = model.score(X, y)
    
    # Calculate p-value for slope
    # t = slope / SE(slope)
    # SE(slope) = sqrt(MSE / SSx)
    residuals = y - model.predict(X)
    mse = np.sum(residuals**2) / (len(y) - 2)
    ssx = np.sum((X - np.mean(X))**2)
    se_slope = np.sqrt(mse / ssx) if ssx > 0 else np.inf
    t_stat = slope / se_slope if se_slope != np.inf else 0
    p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=len(y)-2))
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'p_value': float(p_value),
        'r_squared': float(r_squared),
        'sample_size': len(df)
    }

def apply_bonferroni_correction(p_values: List[float], num_tests: int = None) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    adjusted_p = min(p * k, 1.0)
    """
    if num_tests is None:
        num_tests = len(p_values)
    
    corrected = []
    for p in p_values:
        adj = p * num_tests
        corrected.append(min(adj, 1.0))
    
    return corrected

def calculate_vif(dataset_path: str) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for predictors.
    Warn if VIF > 5.0.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file {dataset_path} not found.")
    
    df = pd.read_csv(dataset_path)
    
    # For this simple model, we only have one predictor (perspective_score)
    # VIF for a single predictor is 1.0 (no multicollinearity)
    # But if we had multiple predictors, we'd compute VIF for each
    
    if 'perspective_score' not in df.columns:
        return {}
    
    # VIF for single predictor is 1.0
    vif_score = 1.0
    
    if vif_score > 5.0:
        logger.warning(f"VIF ({vif_score}) exceeds threshold of 5.0. Multicollinearity detected.")
    
    return {'perspective_score': vif_score}

def generate_scatter_plot(dataset_path: str, output_path: str = "data/artifacts/regression_plot.png"):
    """
    Create scatter plot with regression line and 95% CI ribbon.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file {dataset_path} not found.")
    
    df = pd.read_csv(dataset_path)
    
    required_cols = ['perspective_score', 'moral_judgement_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    df = df.dropna(subset=required_cols)
    
    if len(df) < 2:
        logger.warning("Insufficient data points for plotting.")
        return False
    
    X = df['perspective_score'].values
    y = df['moral_judgement_score'].values
    
    # Fit regression
    model = LinearRegression()
    model.fit(X.reshape(-1, 1), y)
    
    # Generate points for regression line
    x_line = np.linspace(X.min(), X.max(), 100)
    y_line = model.predict(x_line.reshape(-1, 1))
    
    # Calculate confidence interval
    y_pred = model.predict(X.reshape(-1, 1))
    residuals = y - y_pred
    mse = np.sum(residuals**2) / (len(y) - 2)
    
    # Standard error of the mean response
    x_mean = np.mean(X)
    ssx = np.sum((X - x_mean)**2)
    
    # Confidence interval for the regression line
    se_line = np.sqrt(mse * (1/len(X) + (x_line - x_mean)**2 / ssx)) if ssx > 0 else np.zeros_like(x_line)
    t_val = stats.t.ppf(0.975, df=len(X)-2)
    ci_upper = y_line + t_val * se_line
    ci_lower = y_line - t_val * se_line
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(X, y, alpha=0.6, label='Data points')
    plt.plot(x_line, y_line, 'r-', label='Regression line')
    plt.fill_between(x_line, ci_lower, ci_upper, color='red', alpha=0.2, label='95% CI')
    
    plt.xlabel('Perspective Score (1st-person density)')
    plt.ylabel('Moral Judgement Score')
    plt.title('Perspective Score vs Moral Judgement')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")
    return True

def run_analysis_pipeline(dataset_path: str) -> Dict[str, Any]:
    """
    Run full analysis pipeline: regression, Bonferroni, VIF, and plot.
    Returns summary dictionary.
    """
    logger.info(f"Running analysis pipeline on {dataset_path}")
    
    # 1. Run regression
    reg_results = run_regression_analysis(dataset_path)
    
    # 2. Apply Bonferroni correction (assuming 1 test for now)
    p_values = [reg_results['p_value']] if reg_results['p_value'] is not None else []
    bonf_p = apply_bonferroni_correction(p_values, num_tests=1)
    bonf_adjusted_p = bonf_p[0] if bonf_p else None
    
    # 3. Calculate VIF
    vif_results = calculate_vif(dataset_path)
    vif_warning = any(v > 5.0 for v in vif_results.values())
    
    # 4. Generate plot
    plot_path = "data/artifacts/regression_plot.png"
    generate_scatter_plot(dataset_path, plot_path)
    
    # 5. Compile results
    results = {
        'slope': reg_results['slope'],
        'intercept': reg_results['intercept'],
        'p_value': reg_results['p_value'],
        'r_squared': reg_results['r_squared'],
        'bonferroni_adjusted_p': bonf_adjusted_p,
        'sample_size': reg_results['sample_size'],
        'vif_warning': vif_warning
    }
    
    logger.info(f"Analysis results: {results}")
    return results

def run_sensitivity_sweep(matching_results_path: str, thresholds_path: str, dataset_path: str) -> Dict[str, Any]:
    """
    Run sensitivity analysis across thresholds.
    For each threshold: filter matches, join with dataset, run regression, record slope.
    """
    logger.info("Running sensitivity sweep...")
    
    # Load data
    with open(matching_results_path, 'r') as f:
        matching_results = json.load(f)
    
    with open(thresholds_path, 'r') as f:
        thresholds_data = json.load(f)
        thresholds = thresholds_data['thresholds']
    
    df_full = pd.read_csv(dataset_path)
    
    slopes = []
    sample_sizes = []
    
    for threshold in thresholds:
        # Filter matches for this threshold
        filtered = [m for m in matching_results if m.get('threshold_used') == threshold and m.get('similarity_score', 0) >= threshold]
        
        if not filtered:
            logger.warning(f"No matches found for threshold {threshold}.")
            slopes.append(None)
            sample_sizes.append(0)
            continue
        
        # Get unique story_ids from filtered matches
        story_ids = list(set(m['story_id'] for m in filtered))
        
        # Join with full dataset
        temp_df = df_full[df_full['story_id'].isin(story_ids)].copy()
        
        # Check sample size
        if len(temp_df) < 10:
            logger.warning(f"Sample size ({len(temp_df)}) insufficient for regression at threshold {threshold}.")
            slopes.append(None)
            sample_sizes.append(len(temp_df))
            continue
        
        # Save temporary CSV
        temp_path = f"data/processed/temp_sweep_{threshold}.csv"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        temp_df.to_csv(temp_path, index=False)
        
        # Run regression
        try:
            reg_results = run_regression_analysis(temp_path)
            slopes.append(reg_results['slope'])
        except Exception as e:
            logger.error(f"Regression failed for threshold {threshold}: {e}")
            slopes.append(None)
        
        sample_sizes.append(len(temp_df))
    
    # Calculate slope variance
    valid_slopes = [s for s in slopes if s is not None]
    slope_variance = np.var(valid_slopes) if len(valid_slopes) > 1 else 0.0
    
    results = {
        'thresholds': thresholds,
        'slopes': slopes,
        'sample_sizes': sample_sizes,
        'slope_variance': float(slope_variance)
    }
    
    logger.info(f"Sensitivity sweep complete. Variance: {slope_variance}")
    return results
