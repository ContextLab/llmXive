"""Analysis module for correlation and regression."""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LassoCV
from sklearn.model_selection import KFold, cross_val_score
from scipy import stats

# Import from local modules
from config import get_config

logger = logging.getLogger(__name__)

def get_data_path(filename: str) -> Path:
    """Get path to data file."""
    config = get_config()
    return Path(config["data_dir"]) / "processed" / filename

def load_standard_subset() -> pd.DataFrame:
    """Load the standard subset of data."""
    path = get_data_path("standard_subset.csv")
    if not path.exists():
        raise FileNotFoundError(f"Standard subset not found at {path}")
    return pd.read_csv(path)

def compute_correlation_matrix(df: pd.DataFrame, features: List[str], target: str) -> pd.DataFrame:
    """Compute correlation matrix between features and target."""
    data = df[features + [target]].dropna()
    return data.corr()

def compute_p_values(df: pd.DataFrame, features: List[str], target: str) -> Dict[str, float]:
    """Compute p-values for correlations."""
    data = df[features + [target]].dropna()
    p_values = {}
    for feature in features:
        corr, p = stats.pearsonr(data[feature], data[target])
        p_values[feature] = p
    return p_values

def identify_significant_correlations(p_values: Dict[str, float], alpha: float = 0.05) -> List[str]:
    """Identify features with significant correlations."""
    return [f for f, p in p_values.items() if p < alpha]

def run_mlr(df: pd.DataFrame, features: List[str], target: str) -> Dict[str, Any]:
    """Run Multiple Linear Regression."""
    data = df[features + [target]].dropna()
    if len(data) < 2:
        raise ValueError("Not enough data points for MLR")
    
    X = data[features]
    y = data[target]
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R-squared
    y_pred = model.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # Calculate p-values for coefficients
    n = len(y)
    p_values = []
    for i, coef in enumerate(model.coef_):
        # Simple t-test approximation for p-value
        # Standard error of coefficient
        # This is a simplified version; statsmodels would be better but we use sklearn
        se = np.sqrt(np.sum((y - y_pred) ** 2) / (n - len(features) - 1) * np.linalg.inv(X.T @ X)[i, i])
        t_stat = coef / se if se != 0 else 0
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), n - len(features) - 1))
        p_values.append(p_val)
    
    return {
        "coefficients": dict(zip(features, model.coef_.tolist())),
        "intercept": float(model.intercept_),
        "r2": float(r2),
        "p_values": dict(zip(features, p_values))
    }

def run_lasso_regression(df: pd.DataFrame, features: List[str], target: str) -> Dict[str, Any]:
    """Run LASSO regression with K-fold cross-validation."""
    data = df[features + [target]].dropna()
    if len(data) < 2:
        raise ValueError("Not enough data points for LASSO")
    
    X = data[features].values
    y = data[target].values
    
    # Determine K
    n = len(y)
    k = min(5, n - 1)  # Default 5, but max n-1
    if k < 2:
        k = 2 # Minimum 2 folds if possible
    
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    
    # Grid search for alpha
    alphas = [0.01, 0.1, 1.0]
    best_alpha = alphas[0]
    best_score = -np.inf
    
    for alpha in alphas:
        lasso = LassoCV(alphas=[alpha], cv=kf, random_state=42, max_iter=1000)
        scores = cross_val_score(lasso, X, y, cv=kf, scoring='r2')
        mean_score = np.mean(scores)
        if mean_score > best_score:
            best_score = mean_score
            best_alpha = alpha
    
    # Fit final model with best alpha
    final_model = LassoCV(alphas=[best_alpha], cv=kf, random_state=42, max_iter=1000)
    final_model.fit(X, y)
    
    y_pred = final_model.predict(X)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        "coefficients": dict(zip(features, final_model.coef_.tolist())),
        "intercept": float(final_model.intercept_),
        "r2": float(r2),
        "best_alpha": float(best_alpha),
        "cv_r2_mean": float(best_score)
    }

def perform_residual_diagnostics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """Perform residual diagnostics (Shapiro-Wilk and Breusch-Pagan)."""
    residuals = y_true - y_pred
    
    # Shapiro-Wilk test for normality
    shapiro_stat, shapiro_p = stats.shapiro(residuals)
    
    # Breusch-Pagan test for homoscedasticity
    # Note: This requires the fitted values as the explanatory variable
    # We'll use a simple implementation or fallback if statsmodels is not available
    try:
        import statsmodels.api as sm
        from statsmodels.stats.diagnostic import het_breuschpagan
        
        # Breusch-Pagan test
        bp_test = het_breuschpagan(residuals, sm.add_constant(y_pred))
        bp_lm = bp_test[0]
        bp_pvalue = bp_test[1]
    except ImportError:
        # Fallback if statsmodels not available (though it should be in requirements)
        # Simple test: correlation between residuals and fitted values
        corr, bp_pvalue = stats.pearsonr(residuals, y_pred)
        bp_lm = None # Not applicable in fallback
    
    return {
        "shapiro_statistic": float(shapiro_stat),
        "shapiro_p_value": float(shapiro_p),
        "breusch_pagan_statistic": float(bp_lm) if bp_lm is not None else None,
        "breusch_pagan_p_value": float(bp_pvalue)
    }

def verify_correlation_significance(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, bool]:
    """Verify significance of correlations."""
    return {f: p < alpha for f, p in p_values.items()}

def verify_residual_diagnostics(diagnostics: Dict[str, Any], alpha: float = 0.05) -> Dict[str, bool]:
    """Verify residual diagnostics results."""
    return {
        "normality": diagnostics["shapiro_p_value"] > alpha,
        "homoscedasticity": diagnostics["breusch_pagan_p_value"] > alpha
    }

def synthesize_conclusion(
    mlr_results: Dict[str, Any],
    lasso_results: Dict[str, Any],
    diagnostics: Dict[str, Any],
    significant_features: List[str]
) -> str:
    """Synthesize a conclusion from the analysis results."""
    conclusion = []
    
    conclusion.append(f"Multiple Linear Regression R²: {mlr_results['r2']:.4f}")
    conclusion.append(f"LASSO Regression R²: {lasso_results['r2']:.4f}")
    conclusion.append(f"Significant features (p < 0.05): {', '.join(significant_features) if significant_features else 'None'}")
    
    if diagnostics["shapiro_p_value"] > 0.05:
        conclusion.append("Residuals appear normally distributed (Shapiro-Wilk p > 0.05).")
    else:
        conclusion.append("Residuals do not appear normally distributed (Shapiro-Wilk p <= 0.05).")
        
    if diagnostics["breusch_pagan_p_value"] > 0.05:
        conclusion.append("Homoscedasticity assumption holds (Breusch-Pagan p > 0.05).")
    else:
        conclusion.append("Homoscedasticity assumption may be violated (Breusch-Pagan p <= 0.05).")
        
    return " ".join(conclusion)

def save_analysis_results(
    mlr_results: Dict[str, Any],
    lasso_results: Dict[str, Any],
    diagnostics: Dict[str, Any],
    significant_features: List[str],
    output_path: Path
) -> None:
    """Save analysis results to JSON file."""
    results = {
        "mlr": mlr_results,
        "lasso": lasso_results,
        "residual_diagnostics": diagnostics,
        "significant_features": significant_features,
        "conclusion": synthesize_conclusion(mlr_results, lasso_results, diagnostics, significant_features)
    }
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Main entry point for analysis."""
    try:
        # Load data
        df = load_standard_subset()
        
        # Define features and target
        features = ["TPSA", "Rotatable_Bond_Count", "MW", "Aromatic_Ring_Count", "Wiener_Index", "Zagreb_Index"]
        target = "half_life"
        
        # Check if target exists
        if target not in df.columns:
            logger.error(f"Target column '{target}' not found in data.")
            return
        
        # Compute correlations
        corr_matrix = compute_correlation_matrix(df, features, target)
        p_values = compute_p_values(df, features, target)
        significant_features = identify_significant_correlations(p_values)
        
        # Run MLR
        mlr_results = run_mlr(df, features, target)
        
        # Run LASSO
        lasso_results = run_lasso_regression(df, features, target)
        
        # Perform residual diagnostics
        # Get predictions from MLR for diagnostics
        data = df[features + [target]].dropna()
        X = data[features]
        y = data[target]
        model = LinearRegression()
        model.fit(X, y)
        y_pred = model.predict(X)
        
        diagnostics = perform_residual_diagnostics(y.values, y_pred)
        
        # Verify results
        verify_corr = verify_correlation_significance(p_values)
        verify_diag = verify_residual_diagnostics(diagnostics)
        
        # Save results
        output_path = get_data_path("analysis_results.json")
        save_analysis_results(mlr_results, lasso_results, diagnostics, significant_features, output_path)
        
        logger.info("Analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
