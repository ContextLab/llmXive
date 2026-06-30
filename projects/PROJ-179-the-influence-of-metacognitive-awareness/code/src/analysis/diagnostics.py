"""
Diagnostic tests for hierarchical regression (T021).

Implements:
- Normality of residuals (Shapiro-Wilk)
- Homoscedasticity (Breusch-Pagan)
- Collinearity (VIF calculation with flagging)

Output: Writes diagnostic results to data/results/regression_diagnostics.json
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy.stats import shapiro
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config.env_config import load_config, AppConfig

# Setup logging
logger = logging.getLogger(__name__)

def load_regression_results(results_path: str) -> Optional[Dict[str, Any]]:
    """Load regression results from JSON file."""
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Regression results file not found: {results_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in regression results: {e}")
        return None

def load_trial_data(data_path: str) -> Optional[pd.DataFrame]:
    """Load trial data for diagnostics."""
    try:
        return pd.read_csv(data_path)
    except FileNotFoundError:
        logger.error(f"Trial data file not found: {data_path}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Trial data file is empty: {data_path}")
        return None

def check_normality_of_residuals(residuals: np.ndarray) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality of residuals.
    
    Args:
        residuals: Array of residuals from the regression model.
        
    Returns:
        Dictionary with test results.
    """
    if len(residuals) < 3:
        return {
            "test": "shapiro_wilk",
            "status": "SKIP",
            "reason": "Sample size too small (< 3)",
            "statistic": None,
            "p_value": None,
            "is_normal": None
        }
    
    try:
        stat, p_value = shapiro(residuals)
        is_normal = p_value > 0.05  # Fail to reject null hypothesis (normal)
        
        return {
            "test": "shapiro_wilk",
            "status": "PASS",
            "statistic": float(stat),
            "p_value": float(p_value),
            "is_normal": is_normal,
            "interpretation": "Normal" if is_normal else "Non-normal"
        }
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}")
        return {
            "test": "shapiro_wilk",
            "status": "FAIL",
            "reason": str(e),
            "statistic": None,
            "p_value": None,
            "is_normal": None
        }

def check_homoscedasticity(y: np.ndarray, residuals: np.ndarray) -> Dict[str, Any]:
    """
    Perform Breusch-Pagan test for homoscedasticity.
    
    Args:
        y: Dependent variable values.
        residuals: Residuals from the regression model.
        
    Returns:
        Dictionary with test results.
    """
    if len(residuals) < 3:
        return {
            "test": "breusch_pagan",
            "status": "SKIP",
            "reason": "Sample size too small (< 3)",
            "lm_statistic": None,
            "p_value": None,
            "is_homoscedastic": None
        }
    
    try:
        # Breusch-Pagan test
        # Note: het_breuschpagan expects (residuals, exog) where exog are the independent variables
        # We use y as a proxy for exog if we don't have the original design matrix
        lm_stat, lm_p, f_stat, f_p = het_breuschpagan(residuals, y.reshape(-1, 1))
        
        is_homoscedastic = lm_p > 0.05  # Fail to reject null hypothesis (homoscedastic)
        
        return {
            "test": "breusch_pagan",
            "status": "PASS",
            "lm_statistic": float(lm_stat),
            "lm_p_value": float(lm_p),
            "f_statistic": float(f_stat),
            "f_p_value": float(f_p),
            "is_homoscedastic": is_homoscedastic,
            "interpretation": "Homoscedastic" if is_homoscedastic else "Heteroscedastic"
        }
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {e}")
        return {
            "test": "breusch_pagan",
            "status": "FAIL",
            "reason": str(e),
            "lm_statistic": None,
            "p_value": None,
            "is_homoscedastic": None
        }

def calculate_vif(df: pd.DataFrame, feature_columns: list) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing the features.
        feature_columns: List of column names to calculate VIF for.
        
    Returns:
        Dictionary with VIF results and flags.
    """
    if len(feature_columns) == 0:
        return {
            "test": "vif",
            "status": "SKIP",
            "reason": "No features provided",
            "vif_values": {},
            "max_vif": None,
            "collinearity_flag": False,
            "flagged_features": []
        }
    
    try:
        # Filter to only the requested columns
        X = df[feature_columns].dropna()
        
        if X.empty:
            return {
                "test": "vif",
                "status": "SKIP",
                "reason": "No valid data after filtering",
                "vif_values": {},
                "max_vif": None,
                "collinearity_flag": False,
                "flagged_features": []
            }
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        vif_values = {}
        flagged_features = []
        
        for col in X.columns:
            vif = variance_inflation_factor(X_with_const.values, X_with_const.columns.get_loc(col))
            vif_values[col] = float(vif)
            
            if vif >= 5.0:
                flagged_features.append(col)
        
        max_vif = max(vif_values.values()) if vif_values else 0.0
        collinearity_flag = any(v >= 5.0 for v in vif_values.values())
        
        return {
            "test": "vif",
            "status": "PASS",
            "vif_values": vif_values,
            "max_vif": float(max_vif),
            "collinearity_flag": collinearity_flag,
            "flagged_features": flagged_features,
            "threshold": 5.0,
            "interpretation": "High collinearity detected" if collinearity_flag else "No high collinearity"
        }
    except Exception as e:
        logger.warning(f"VIF calculation failed: {e}")
        return {
            "test": "vif",
            "status": "FAIL",
            "reason": str(e),
            "vif_values": {},
            "max_vif": None,
            "collinearity_flag": False,
            "flagged_features": []
        }

def run_diagnostics(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run all diagnostic tests on the regression model.
    
    Args:
        config: Optional configuration dictionary. If None, loads from default config.
        
    Returns:
        Dictionary containing all diagnostic results.
    """
    if config is None:
        config = load_config()
    
    # Determine paths
    base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
    results_dir = Path(base_dir) / config.get("paths", {}).get("results", "data/results")
    derived_dir = Path(base_dir) / config.get("paths", {}).get("derived_data", "data/derived")
    
    results_dir.mkdir(parents=True, exist_ok=True)
    
    regression_results_path = results_dir / "regression_analysis.json"
    trial_data_path = derived_dir / "trial_data.csv"
    
    logger.info(f"Loading regression results from {regression_results_path}")
    regression_results = load_regression_results(str(regression_results_path))
    
    if regression_results is None:
        logger.error("Cannot run diagnostics: regression results not found")
        return {
            "status": "ERROR",
            "reason": "Regression results file not found",
            "diagnostics": {}
        }
    
    # Extract residuals and features from regression results
    residuals = regression_results.get("residuals", [])
    if not residuals:
        logger.warning("No residuals found in regression results")
        residuals = []
    
    # Try to load trial data for VIF calculation
    trial_data = load_trial_data(str(trial_data_path))
    
    diagnostics = {
        "status": "COMPLETE",
        "input_files": {
            "regression_results": str(regression_results_path),
            "trial_data": str(trial_data_path) if trial_data is not None else None
        },
        "diagnostics": {}
    }
    
    # 1. Normality of residuals
    logger.info("Running Shapiro-Wilk test for normality...")
    if residuals:
        normality_result = check_normality_of_residuals(np.array(residuals))
    else:
        normality_result = {
            "test": "shapiro_wilk",
            "status": "SKIP",
            "reason": "No residuals provided",
            "statistic": None,
            "p_value": None,
            "is_normal": None
        }
    diagnostics["diagnostics"]["normality"] = normality_result
    
    # 2. Homoscedasticity
    logger.info("Running Breusch-Pagan test for homoscedasticity...")
    # We need y values for BP test. Try to extract from regression results or trial data
    y_values = regression_results.get("y_values", [])
    if not y_values and trial_data is not None and 'd_prime' in trial_data.columns:
        y_values = trial_data['d_prime'].dropna().values
    
    if y_values and residuals:
        # Ensure lengths match
        min_len = min(len(y_values), len(residuals))
        y_subset = np.array(y_values[:min_len])
        res_subset = np.array(residuals[:min_len])
        homoscedasticity_result = check_homoscedasticity(y_subset, res_subset)
    else:
        homoscedasticity_result = {
            "test": "breusch_pagan",
            "status": "SKIP",
            "reason": "Insufficient data for homoscedasticity test",
            "lm_statistic": None,
            "p_value": None,
            "is_homoscedastic": None
        }
    diagnostics["diagnostics"]["homoscedasticity"] = homoscedasticity_result
    
    # 3. Collinearity (VIF)
    logger.info("Calculating VIF for collinearity...")
    if trial_data is not None:
        # Identify feature columns used in regression
        # Common features: age, gender_encoded, working_memory, meta_auc
        feature_candidates = ['age', 'gender_encoded', 'working_memory', 'meta_auc', 'metacognitive_score']
        available_features = [col for col in feature_candidates if col in trial_data.columns]
        
        if available_features:
            vif_result = calculate_vif(trial_data, available_features)
        else:
            vif_result = {
                "test": "vif",
                "status": "SKIP",
                "reason": f"No feature columns found. Candidates: {feature_candidates}",
                "vif_values": {},
                "max_vif": None,
                "collinearity_flag": False,
                "flagged_features": []
            }
    else:
        vif_result = {
            "test": "vif",
            "status": "SKIP",
            "reason": "Trial data not available",
            "vif_values": {},
            "max_vif": None,
            "collinearity_flag": False,
            "flagged_features": []
        }
    diagnostics["diagnostics"]["collinearity"] = vif_result
    
    # Summary
    diagnostics["summary"] = {
        "normality_passed": normality_result.get("is_normal", False),
        "homoscedasticity_passed": homoscedasticity_result.get("is_homoscedastic", False),
        "collinearity_flagged": vif_result.get("collinearity_flag", False),
        "all_checks_passed": (
            normality_result.get("is_normal", False) and
            homoscedasticity_result.get("is_homoscedastic", False) and
            not vif_result.get("collinearity_flag", False)
        )
    }
    
    # Write output
    output_path = results_dir / "regression_diagnostics.json"
    with open(output_path, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    
    logger.info(f"Diagnostics written to {output_path}")
    return diagnostics

def main():
    """Main entry point for diagnostic analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting diagnostic analysis (T021)...")
    
    try:
        config = load_config()
        results = run_diagnostics(config)
        
        if results["status"] == "ERROR":
            logger.error(f"Diagnostics failed: {results.get('reason', 'Unknown error')}")
            sys.exit(1)
        
        logger.info("Diagnostics completed successfully.")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Unexpected error during diagnostics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()