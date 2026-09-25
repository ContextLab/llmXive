"""
Diagnostic plots for OLS regression model.

Generates Residuals vs Fitted, Q-Q plot, and Scale-Location plot
to assess model assumptions (linearity, normality of residuals, homoscedasticity).
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.outliers_influence import OLSInfluence
import statsmodels.api as sm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root and paths
from config import get_project_root
PROJECT_ROOT = get_project_root()
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
DIAGNOSTICS_DIR = PROCESSED_DATA_DIR / "diagnostics"
CENTERED_DATA_PATH = PROCESSED_DATA_DIR / "centered_data.parquet"
INTERACTION_RESULTS_PATH = PROCESSED_DATA_DIR / "interaction_results.json"
DIAGNOSTICS_REPORT_PATH = PROCESSED_DATA_DIR / "model_diagnostics_report.json"

def ensure_directories() -> None:
    """Create the diagnostics directory if it doesn't exist."""
    DIAGNOSTICS_DIR.mkdir(parents=True, exist_ok=True)

def load_centered_data() -> pd.DataFrame:
    """Load the centered dataset used for regression."""
    if not CENTERED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Centered data file not found at {CENTERED_DATA_PATH}. "
            "Please run T021 (transform_and_center) first."
        )
    logger.info(f"Loading centered data from {CENTERED_DATA_PATH}")
    return pd.read_parquet(CENTERED_DATA_PATH)

def load_interaction_results() -> Dict[str, Any]:
    """Load the interaction results to check significance."""
    if not INTERACTION_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Interaction results file not found at {INTERACTION_RESULTS_PATH}. "
            "Please run T024 first."
        )
    with open(INTERACTION_RESULTS_PATH, 'r') as f:
        return json.load(f)

def run_ols_regression(df: pd.DataFrame) -> sm.OLSResults:
    """
    Run the OLS regression model as defined in T022.
    
    Args:
        df: The centered dataframe containing predictors and outcome.
        
    Returns:
        Fitted OLS results object.
    """
    # Reconstruct the formula logic from T022
    # Base formula: procrastination ~ log_k + wm_metric + log_k:wm_metric
    # Covariates: age, gender (if present)
    
    # Determine which covariates are present
    covariates = []
    if 'age' in df.columns:
        covariates.append('age')
    if 'gender' in df.columns:
        covariates.append('gender')
        
    # Build formula
    predictors = ['log_k', 'wm_metric', 'log_k:wm_metric']
    formula_parts = predictors + covariates
    formula = f"procrastination ~ {' + '.join(formula_parts)}"
    
    logger.info(f"Running OLS regression with formula: {formula}")
    
    try:
        model = sm.formula.ols(formula=formula, data=df)
        results = model.fit()
        return results
    except Exception as e:
        logger.error(f"OLS regression failed: {e}")
        raise

def plot_residuals_vs_fitted(results: sm.OLSResults, save_path: Path) -> Dict[str, Any]:
    """
    Generate Residuals vs Fitted plot.
    
    Args:
        results: Fitted OLS results.
        save_path: Path to save the plot.
        
    Returns:
        Dictionary with visual inspection results.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    fitted = results.fittedvalues
    residuals = results.resid
    
    ax.scatter(fitted, residuals, alpha=0.6, edgecolors='w', s=50)
    ax.axhline(0, color='red', linestyle='--', linewidth=2)
    
    # Add a lowess smooth line to detect patterns
    if len(fitted) > 0:
        lowess = sm.nonparametric.lowess(residuals, fitted, frac=0.3)
        ax.plot(lowess[:, 0], lowess[:, 1], color='blue', linewidth=2, label='Lowess Smooth')
    
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel('Residuals')
    ax.set_title('Residuals vs Fitted')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close(fig)
    
    # Visual inspection: check for patterns
    # Ideally, residuals should be randomly scattered around 0
    # We check correlation between fitted and residuals
    corr, p_value = stats.pearsonr(fitted, residuals)
    
    inspection = {
        "plot_type": "residuals_vs_fitted",
        "correlation_fitted_residuals": float(corr),
        "p_value": float(p_value),
        "interpretation": "No pattern" if p_value > 0.05 else "Pattern detected (heteroscedasticity or non-linearity)"
    }
    
    logger.info(f"Residuals vs Fitted: correlation={corr:.4f}, p={p_value:.4f}")
    return inspection

def plot_q_q_plot(results: sm.OLSResults, save_path: Path) -> Dict[str, Any]:
    """
    Generate Q-Q plot for normality of residuals.
    
    Args:
        results: Fitted OLS results.
        save_path: Path to save the plot.
        
    Returns:
        Dictionary with visual inspection results.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sm.qqplot(results.resid, line='45', fit=True, ax=ax)
    ax.set_title('Normal Q-Q')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close(fig)
    
    # Statistical test for normality (Shapiro-Wilk)
    # Note: Shapiro-Wilk has a limit of 5000 samples, so we sample if needed
    residuals = results.resid
    if len(residuals) > 5000:
        sample_indices = np.random.choice(len(residuals), 5000, replace=False)
        sample_residuals = residuals.iloc[sample_indices] if hasattr(residuals, 'iloc') else residuals[sample_indices]
        stat, p_value = stats.shapiro(sample_residuals)
    else:
        stat, p_value = stats.shapiro(residuals)
    
    inspection = {
        "plot_type": "qq_plot",
        "shapiro_statistic": float(stat),
        "shapiro_p_value": float(p_value),
        "interpretation": "Normal" if p_value > 0.05 else "Non-normal residuals"
    }
    
    logger.info(f"Q-Q Plot: Shapiro-Wilk p={p_value:.4f}")
    return inspection

def plot_scale_location(results: sm.OLSResults, save_path: Path) -> Dict[str, Any]:
    """
    Generate Scale-Location plot (Square root of standardized residuals vs Fitted).
    
    Args:
        results: Fitted OLS results.
        save_path: Path to save the plot.
        
    Returns:
        Dictionary with visual inspection results.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    fitted = results.fittedvalues
    standardized_residuals = results.get_influence().resid_studentized_internal
    sqrt_std_resid = np.sqrt(np.abs(standardized_residuals))
    
    ax.scatter(fitted, sqrt_std_resid, alpha=0.6, edgecolors='w', s=50)
    
    # Add lowess smooth line
    if len(fitted) > 0:
        lowess = sm.nonparametric.lowess(sqrt_std_resid, fitted, frac=0.3)
        ax.plot(lowess[:, 0], lowess[:, 1], color='red', linewidth=2, label='Lowess Smooth')
    
    ax.set_xlabel('Fitted Values')
    ax.set_ylabel(r'$\sqrt{|Standardized Residuals|}$')
    ax.set_title('Scale-Location')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close(fig)
    
    # Check for trend in scale (heteroscedasticity)
    corr, p_value = stats.pearsonr(fitted, sqrt_std_resid)
    
    inspection = {
        "plot_type": "scale_location",
        "correlation_fitted_sqrt_resid": float(corr),
        "p_value": float(p_value),
        "interpretation": "Homoscedasticity" if p_value > 0.05 else "Heteroscedasticity detected"
    }
    
    logger.info(f"Scale-Location: correlation={corr:.4f}, p={p_value:.4f}")
    return inspection

def generate_diagnostics_report(inspections: list) -> Dict[str, Any]:
    """
    Aggregate all inspection results into a final report.
    
    Args:
        inspections: List of inspection dictionaries.
        
    Returns:
        Dictionary containing the full diagnostics report.
    """
    report = {
        "model_assumptions_check": {
            "linearity_and_homoscedasticity": inspections[0],
            "normality_of_residuals": inspections[1],
            "scale_location_check": inspections[2]
        },
        "summary": {
            "all_assumptions_met": all(
                "No pattern" in i["interpretation"] or 
                "Normal" in i["interpretation"] or 
                "Homoscedasticity" in i["interpretation"] 
                for i in inspections
            ),
            "plots_generated": [
                "residuals.png",
                "qq_plot.png",
                "scale_location.png"
            ]
        }
    }
    return report

def run_diagnostics() -> None:
    """
    Main function to run all diagnostic plots and generate the report.
    """
    logger.info("Starting model diagnostics generation...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load data
    df = load_centered_data()
    
    # Run regression
    results = run_ols_regression(df)
    
    # Define output paths
    residuals_path = DIAGNOSTICS_DIR / "residuals.png"
    qq_path = DIAGNOSTICS_DIR / "qq_plot.png"
    scale_path = DIAGNOSTICS_DIR / "scale_location.png"
    
    # Generate plots and collect inspections
    inspections = []
    
    logger.info("Generating Residuals vs Fitted plot...")
    inspections.append(plot_residuals_vs_fitted(results, residuals_path))
    
    logger.info("Generating Q-Q plot...")
    inspections.append(plot_q_q_plot(results, qq_path))
    
    logger.info("Generating Scale-Location plot...")
    inspections.append(plot_scale_location(results, scale_path))
    
    # Generate report
    report = generate_diagnostics_report(inspections)
    
    # Save report
    with open(DIAGNOSTICS_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Diagnostics report saved to {DIAGNOSTICS_REPORT_PATH}")
    logger.info(f"Plots saved to {DIAGNOSTICS_DIR}")
    
    # Print summary
    print("\n=== Model Diagnostics Summary ===")
    print(f"Linearity/Homoscedasticity: {inspections[0]['interpretation']}")
    print(f"Normality: {inspections[1]['interpretation']}")
    print(f"Scale-Location: {inspections[2]['interpretation']}")
    print(f"All Assumptions Met: {report['summary']['all_assumptions_met']}")
    print("================================\n")

def main():
    """Entry point for the script."""
    try:
        run_diagnostics()
    except FileNotFoundError as e:
        logger.error(f"Missing required data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during diagnostics generation: {e}")
        raise

if __name__ == "__main__":
    main()
