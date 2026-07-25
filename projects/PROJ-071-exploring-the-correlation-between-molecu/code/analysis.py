import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

# Import fallback module
from scipy_fallback import (
    shapiro_wilk_test, 
    breusch_pagan_test, 
    run_residual_diagnostics_scipy
)

# Configure logging
logger = logging.getLogger(__name__)

def get_data_path():
    """Get the project root data path."""
    return Path(__file__).parent.parent / "data"

def load_standard_subset():
    """Load the standard subset of data for analysis."""
    data_path = get_data_path()
    file_path = data_path / "processed" / "standard_subset.csv"
    
    if not file_path.exists():
        logger.error(f"Standard subset file not found: {file_path}")
        return pd.DataFrame()
        
    df = pd.read_csv(file_path)
    logger.info(f"Loaded standard subset with {len(df)} rows")
    return df

def compute_correlation_matrix(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """Compute Pearson correlation matrix for specified features."""
    if df.empty:
        return pd.DataFrame()
        
    # Filter for features that exist and have non-zero variance
    valid_features = []
    for f in features:
        if f in df.columns and df[f].var() > 1e-9:
            valid_features.append(f)
        else:
            logger.warning(f"Skipped feature {f}: missing or zero variance")
    
    if len(valid_features) < 2:
        logger.warning("Not enough features with variance to compute correlation matrix")
        return pd.DataFrame()
    
    return df[valid_features].corr(method='pearson')

def compute_p_values(df: pd.DataFrame, features: List[str]) -> Dict[str, Dict[str, float]]:
    """Compute p-values for Pearson correlations."""
    p_values = {}
    
    if df.empty:
        return p_values
        
    valid_features = [f for f in features if f in df.columns and df[f].var() > 1e-9]
    
    for i, f1 in enumerate(valid_features):
        p_values[f1] = {}
        for f2 in valid_features:
            if f1 == f2:
                continue
            # Calculate p-value for correlation
            corr, p_val = scipy_stats.pearsonr(df[f1], df[f2])
            p_values[f1][f2] = p_val
            
    return p_values

def identify_significant_correlations(correlations: pd.DataFrame, p_values: Dict, threshold_r: float = 0.5, threshold_p: float = 0.05) -> List[Dict]:
    """Identify correlation pairs that meet significance thresholds."""
    significant = []
    
    if correlations.empty:
        return significant
        
    for f1 in correlations.columns:
        for f2 in correlations.columns:
            if f1 >= f2: # Avoid duplicates and self
                continue
                
            r = correlations.loc[f1, f2]
            p = p_values.get(f1, {}).get(f2, 1.0)
            
            if abs(r) >= threshold_r and p < threshold_p:
                significant.append({
                    "feature_1": f1,
                    "feature_2": f2,
                    "correlation": r,
                    "p_value": p
                })
                
    return significant

def run_mlr(df: pd.DataFrame, target: str, features: List[str]) -> Dict[str, Any]:
    """Run Multiple Linear Regression."""
    if df.empty:
        return {"error": "Empty dataframe"}
        
    X = df[features].values
    y = df[target].values
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X])
    
    # Check for singularity
    try:
        beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        logger.warning("Singular matrix in MLR. Using pseudo-inverse.")
        beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
        
    y_pred = X_with_intercept @ beta
    residuals = y - y_pred
    
    # R-squared
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        "coefficients": beta.tolist(),
        "r_squared": r2,
        "residuals": residuals.tolist(),
        "fitted_values": y_pred.tolist()
    }

def run_lasso_regression(df: pd.DataFrame, target: str, features: List[str]) -> Dict[str, Any]:
    """Run LASSO regression with cross-validation."""
    from sklearn.linear_model import LassoCV
    
    if df.empty:
        return {"error": "Empty dataframe"}
        
    X = df[features].values
    y = df[target].values
    
    n_samples = len(X)
    # Dynamic K: min(5, n-1)
    k_folds = min(5, n_samples - 1) if n_samples > 1 else 1
    
    try:
        model = LassoCV(cv=k_folds, alphas=[0.01, 0.1, 1.0], random_state=42)
        model.fit(X, y)
        
        y_pred = model.predict(X)
        residuals = y - y_pred
        
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            "best_alpha": model.alpha_,
            "r_squared": r2,
            "coefficients": model.coef_.tolist(),
            "residuals": residuals.tolist(),
            "fitted_values": y_pred.tolist(),
            "cv_folds": k_folds
        }
    except Exception as e:
        logger.error(f"LASSO regression failed: {e}")
        return {"error": str(e)}

def perform_residual_diagnostics(residuals: np.ndarray, fitted_values: np.ndarray) -> Dict[str, Any]:
    """
    Perform residual diagnostics using scipy fallbacks.
    
    This function integrates the scipy fallback implementations for 
    Shapiro-Wilk and Breusch-Pagan tests.
    """
    logger.info("Performing residual diagnostics using scipy fallback...")
    return run_residual_diagnostics_scipy(residuals, fitted_values)

def verify_correlation_significance(significant_correlations: List[Dict]) -> Dict[str, Any]:
    """Verify and log correlation significance."""
    passed = len(significant_correlations) > 0
    return {
        "count": len(significant_correlations),
        "passed": passed,
        "details": significant_correlations
    }

def verify_residual_diagnostics(diagnostics: Dict[str, Any]) -> Dict[str, Any]:
    """Verify and log residual diagnostics results."""
    shapiro_pass = diagnostics.get("shapiro_pass", False)
    bp_pass = diagnostics.get("breusch_pagan_pass", False)
    
    return {
        "shapiro_pass": shapiro_pass,
        "breusch_pagan_pass": bp_pass,
        "overall_pass": shapiro_pass and bp_pass,
        "details": diagnostics
    }

def synthesize_conclusion(correlation_result: Dict, diagnostic_result: Dict) -> str:
    """Synthesize the final conclusion based on correlation and diagnostics."""
    if not correlation_result.get("passed", False):
        return "Correlation exists: False (No significant correlations found)"
        
    if not diagnostic_result.get("overall_pass", False):
        return "Correlation exists: True (Significant correlations found, but model assumptions violated)"
        
    return "Correlation exists: True (Significant correlations found, model assumptions met)"

def save_analysis_results(results: Dict[str, Any], output_path: Path):
    """Save analysis results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Main entry point for analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Load data
    df = load_standard_subset()
    if df.empty:
        logger.error("No data available for analysis. Exiting.")
        return
        
    # Define features and target
    # Assuming columns exist based on previous steps
    features = [col for col in df.columns if col not in ['smiles', 'drug_name', 'half_life']]
    target = 'half_life'
    
    if target not in df.columns:
        logger.error(f"Target column '{target}' not found in dataframe.")
        return
        
    # Compute correlations
    corr_matrix = compute_correlation_matrix(df, features)
    p_vals = compute_p_values(df, features)
    significant = identify_significant_correlations(corr_matrix, p_vals)
    
    # Run MLR
    mlr_results = run_mlr(df, target, features[:5]) # Limit features for demo
    
    # Run LASSO
    lasso_results = run_lasso_regression(df, target, features[:5])
    
    # Diagnostics
    if "residuals" in lasso_results:
        residuals = np.array(lasso_results["residuals"])
        fitted = np.array(lasso_results["fitted_values"])
        diagnostics = perform_residual_diagnostics(residuals, fitted)
    else:
        diagnostics = {"error": "No residuals available"}
        
    # Verify
    corr_sig = verify_correlation_significance(significant)
    diag_res = verify_residual_diagnostics(diagnostics)
    
    # Conclusion
    conclusion = synthesize_conclusion(corr_sig, diag_res)
    
    # Prepare final results
    final_results = {
        "correlation_significance": corr_sig,
        "residual_diagnostics": diag_res,
        "correlation_conclusion": conclusion,
        "mlr_results": mlr_results,
        "lasso_results": lasso_results
    }
    
    # Save
    data_path = get_data_path()
    output_file = data_path / "processed" / "analysis_results.json"
    save_analysis_results(final_results, output_file)
    
    logger.info("Analysis complete.")
