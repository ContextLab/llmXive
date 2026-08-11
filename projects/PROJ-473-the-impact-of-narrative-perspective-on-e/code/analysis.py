import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy import stats
from typing import Dict, List, Any, Optional
import logging
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

def run_regression_analysis(dataset_path: str) -> Dict[str, Any]:
    """
    Perform linear regression with perspective_score as predictor 
    and moral_judgement_score as outcome.
    
    Returns dict with slope, intercept, p-value, r-squared.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # Validate required columns
    required_cols = ['perspective_score', 'moral_judgement_score', 'empathy_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with NaN
    df = df.dropna(subset=required_cols)
    
    if len(df) < 3:
        raise ValueError("Insufficient data for regression (need at least 3 rows)")
    
    X = df['perspective_score'].values.reshape(-1, 1)
    y_moral = df['moral_judgement_score'].values
    y_empathy = df['empathy_score'].values
    
    # Regression 1: Perspective -> Moral Judgement
    model_moral = LinearRegression()
    model_moral.fit(X, y_moral)
    slope_moral = model_moral.coef_[0]
    intercept_moral = model_moral.intercept_
    r2_moral = model_moral.score(X, y_moral)
    
    # Calculate p-value for slope
    # t = slope / SE(slope)
    n = len(df)
    residuals = y_moral - model_moral.predict(X)
    mse = np.sum(residuals**2) / (n - 2)
    se_slope = np.sqrt(mse / np.sum((X - np.mean(X))**2))
    t_stat = slope_moral / se_slope
    p_value_moral = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - 2))
    
    # Regression 2: Perspective -> Empathy
    model_empathy = LinearRegression()
    model_empathy.fit(X, y_empathy)
    slope_empathy = model_empathy.coef_[0]
    intercept_empathy = model_empathy.intercept_
    r2_empathy = model_empathy.score(X, y_empathy)
    
    residuals_e = y_empathy - model_empathy.predict(X)
    mse_e = np.sum(residuals_e**2) / (n - 2)
    se_slope_e = np.sqrt(mse_e / np.sum((X - np.mean(X))**2))
    t_stat_e = slope_empathy / se_slope_e
    p_value_empathy = 2 * (1 - stats.t.cdf(np.abs(t_stat_e), n - 2))
    
    return {
        "moral_judgement": {
            "slope": float(slope_moral),
            "intercept": float(intercept_moral),
            "p_value": float(p_value_moral),
            "r_squared": float(r2_moral),
            "n_samples": n
        },
        "empathy": {
            "slope": float(slope_empathy),
            "intercept": float(intercept_empathy),
            "p_value": float(p_value_empathy),
            "r_squared": float(r2_empathy),
            "n_samples": n
        }
    }

def apply_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Adjust p-values based on the number of hypothesis tests performed (α/k).
    """
    k = len(p_values)
    if k == 0:
        return []
    
    corrected = [min(p * k, 1.0) for p in p_values]
    return corrected

def calculate_vif(dataset_path: str) -> Dict[str, float]:
    """
    Calculate VIF for predictors. Warn if VIF > 5.0.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # For this simple model, we only have one predictor (perspective_score)
    # VIF for a single predictor is 1.0 (no multicollinearity possible)
    # But if we had multiple, we'd calculate:
    # VIF = 1 / (1 - R^2) where R^2 is from regressing X_i on other Xs
    
    # Since we only have one predictor, return 1.0
    vif_result = {
        "perspective_score": 1.0
    }
    
    for var, vif_val in vif_result.items():
        if vif_val > 5.0:
            logger.warning(f"High multicollinearity detected for {var}: VIF = {vif_val}")
    
    return vif_result

def generate_scatter_plot(dataset_path: str, output_path: str) -> str:
    """
    Create scatter plot with regression line and 95% CI ribbon.
    Save to output_path.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    df = df.dropna(subset=['perspective_score', 'moral_judgement_score'])
    
    if len(df) < 3:
        raise ValueError("Insufficient data for plotting")
    
    x = df['perspective_score']
    y = df['moral_judgement_score']
    
    # Fit regression
    model = LinearRegression()
    model.fit(x.values.reshape(-1, 1), y)
    y_pred = model.predict(x.values.reshape(-1, 1))
    
    # Calculate 95% CI
    residuals = y - y_pred
    mse = np.sum(residuals**2) / (len(y) - 2)
    x_mean = np.mean(x)
    x_var = np.sum((x - x_mean)**2)
    
    # Standard error of prediction
    se_pred = np.sqrt(mse * (1/len(y) + (x - x_mean)**2 / x_var))
    ci_95 = 1.96 * se_pred
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=x, y=y, alpha=0.6, label='Data')
    plt.plot(x, y_pred, 'r-', label='Regression Line')
    plt.fill_between(x, y_pred - ci_95, y_pred + ci_95, color='r', alpha=0.2, label='95% CI')
    plt.xlabel('Perspective Score (First-Person Density)')
    plt.ylabel('Moral Judgement Score')
    plt.title('Relationship between Narrative Perspective and Moral Judgement')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")
    return output_path

def run_analysis_pipeline(dataset_path: str) -> Dict[str, Any]:
    """
    Run the full analysis pipeline and return summary results.
    """
    logger.info(f"Running analysis pipeline on {dataset_path}")
    
    # Run regression
    regression_results = run_regression_analysis(dataset_path)
    
    # Apply Bonferroni correction to p-values
    p_values = [
        regression_results["moral_judgement"]["p_value"],
        regression_results["empathy"]["p_value"]
    ]
    corrected_p_values = apply_bonferroni_correction(p_values)
    regression_results["moral_judgement"]["p_value_bonferroni"] = corrected_p_values[0]
    regression_results["empathy"]["p_value_bonferroni"] = corrected_p_values[1]
    
    # Calculate VIF
    vif_results = calculate_vif(dataset_path)
    regression_results["vif"] = vif_results
    
    # Generate plot
    plot_path = "data/artifacts/regression_plot.png"
    generate_scatter_plot(dataset_path, plot_path)
    regression_results["plot_path"] = plot_path
    
    # Add summary metadata
    df = pd.read_csv(dataset_path)
    regression_results["summary"] = {
        "total_samples": len(df),
        "perspective_score_mean": float(df['perspective_score'].mean()),
        "perspective_score_std": float(df['perspective_score'].std()),
        "moral_judgement_mean": float(df['moral_judgement_score'].mean()),
        "moral_judgement_std": float(df['moral_judgement_score'].std()),
        "empathy_mean": float(df['empathy_score'].mean()),
        "empathy_std": float(df['empathy_score'].std())
    }
    
    logger.info("Analysis pipeline complete")
    return regression_results
