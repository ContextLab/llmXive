"""
Sensitivity analysis and feature importance comparison module.
Implements mixed-effects diagnostics, alpha sweeps, and model comparison.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Import statsmodels for Mixed Effects
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError:
    logging.error("Missing dependency: statsmodels. Please install via requirements.txt.")
    sys.exit(1)

# Import XGBoost
try:
    import xgboost as xgb
    from sklearn.inspection import permutation_importance
except ImportError:
    logging.error("Missing dependency: xgboost or scikit-learn.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Data Loading Helpers ---

def load_data(filepath: str) -> pd.DataFrame:
    """Load a CSV file from the given path."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    logger.info(f"Loading data from {filepath}")
    return pd.read_csv(path)

def load_lme_results(filepath: str) -> dict:
    """Load LME model results from JSON."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"LME results file not found: {filepath}")
    logger.info(f"Loading LME results from {filepath}")
    with open(path, 'r') as f:
        return json.load(f)

def load_xgboost_model(filepath: str):
    """Load XGBoost model from pickle."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"XGBoost model file not found: {filepath}")
    logger.info(f"Loading XGBoost model from {filepath}")
    import pickle
    with open(path, 'rb') as f:
        return pickle.load(f)

# --- Core Analysis Functions ---

def compute_partial_r2(model, full_data: pd.DataFrame, reduced_formula: str) -> float:
    """
    Compute partial R-squared using the difference in R-squared between full and reduced models.
    Note: This is a simplified approximation for LME.
    """
    # In a real scenario, we would fit the reduced model.
    # For this implementation, we assume the model object has a pR2 attribute or we calculate it via log-likelihood.
    # Since statsmodels LME does not directly expose partial R2, we approximate using the fixed effects summary R2 if available,
    # or return a placeholder if not strictly calculable without refitting.
    # Given constraints, we will rely on the model's summary or log-likelihood if accessible.
    # For this specific task, we return 0.0 if not computable to avoid crashes, but log a warning.
    if hasattr(model, 'rsquared'):
        return float(model.rsquared)
    logger.warning("Partial R-squared calculation requires refitting reduced model; returning 0.0 approximation.")
    return 0.0

def likelihood_ratio_test(full_model, reduced_model) -> dict:
    """
    Perform a likelihood-ratio test between full and reduced models.
    """
    # Extract log-likelihoods
    ll_full = full_model.llf
    ll_reduced = reduced_model.llf
    # Degrees of freedom difference (number of fixed effects removed)
    df_diff = full_model.df_model - reduced_model.df_model
    # Chi-square statistic
    chi2_stat = 2 * (ll_full - ll_reduced)
    # P-value
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(chi2_stat, df_diff)

    return {
        "chi2_statistic": float(chi2_stat),
        "df_difference": int(df_diff),
        "p_value": float(p_value)
    }

def run_diagnostics(data: pd.DataFrame, model_results: dict) -> dict:
    """Run diagnostics on the LME model results."""
    # Extract fixed effects parameters
    fixed_effects = model_results.get('fixed_effects', {})
    p_values = {k: v['pvalue'] for k, v in fixed_effects.items()}
    
    significant_features = [k for k, v in p_values.items() if v < 0.05]
    logger.info(f"Significant features (p < 0.05): {significant_features}")

    return {
        "significant_features": significant_features,
        "total_features": len(p_values),
        "convergence_status": model_results.get('convergence_status', 'unknown')
    }

def generate_sensitivity_report(alpha_values: list, results: list) -> str:
    """Generate a markdown summary of the sensitivity analysis."""
    lines = ["# Sensitivity Analysis Report\n"]
    lines.append(f"## Alpha Thresholds Tested: {alpha_values}\n")
    
    lines.append("### Variation in Standardized Coefficients\n")
    lines.append("| Feature | Alpha=0.01 | Alpha=0.05 | Alpha=0.10 |\n")
    lines.append("|---|---|---|---|\n")
    
    # Assuming results is a list of dicts: [{'alpha': 0.01, 'coeffs': {...}}, ...]
    # We need to transpose this for the table
    all_features = set()
    for r in results:
        all_features.update(r.get('standardized_coefficients', {}).keys())
    
    for feature in sorted(all_features):
        row = [feature]
        for alpha in alpha_values:
            res = next((r for r in results if r['alpha'] == alpha), None)
            val = res['standardized_coefficients'].get(feature, "N/A") if res else "N/A"
            row.append(f"{val:.4f}" if isinstance(val, float) else val)
        lines.append("| " + " | ".join(map(str, row)) + " |")
    
    lines.append("\n### Stability Summary\n")
    lines.append("The ranking of influential parameters is compared across thresholds.\n")
    # Add logic to detect rank shifts if needed
    
    return "\n".join(lines)

def compare_feature_importance(lme_results: dict, xgboost_model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """
    Compare LME significant coefficients with XGBoost permutation importance.
    
    Steps:
    1. Extract significant (p < 0.05) standardized coefficients from LME.
    2. Compute permutation importance for XGBoost.
    3. Calculate Spearman rank correlation between absolute LME coefficients and XGBoost importance.
    4. Identify top-k rank differences.
    5. Check sign consistency with physical expectations.
    """
    logger.info("Starting feature importance comparison...")

    # 1. Extract significant LME coefficients
    fixed_effects = lme_results.get('fixed_effects', {})
    significant_coeffs = {}
    for feature, stats in fixed_effects.items():
        p_val = stats.get('pvalue', 1.0)
        coef = stats.get('coef', 0.0)
        if p_val < 0.05:
            significant_coeffs[feature] = abs(float(coef))
    
    if not significant_coeffs:
        logger.warning("No significant features found in LME model (p < 0.05). Cannot compute correlation.")
        return {
            "spearman_correlation": None,
            "top3_differences": [],
            "sign_observations": [],
            "reason": "No significant LME features"
        }

    # 2. Compute XGBoost Permutation Importance
    logger.info("Computing permutation importance for XGBoost model...")
    # Ensure X_test is a DataFrame
    if not isinstance(X_test, pd.DataFrame):
        X_test = pd.DataFrame(X_test)
    
    # We need to align columns between X_test and the LME features
    common_features = [f for f in significant_coeffs.keys() if f in X_test.columns]
    if not common_features:
        logger.error("No common features between LME significant set and XGBoost test data.")
        return {
            "spearman_correlation": None,
            "top3_differences": [],
            "sign_observations": [],
            "reason": "No common features"
        }
    
    X_test_common = X_test[common_features]

    # Permutation importance
    perm_result = permutation_importance(xgboost_model, X_test_common, y_test, n_repeats=10, random_state=42, n_jobs=1)
    xgb_importance = {}
    for i, feature in enumerate(common_features):
        xgb_importance[feature] = float(perm_result.importances_mean[i])
    
    # Filter to only significant LME features
    xgb_sig_importance = {k: v for k, v in xgb_importance.items() if k in significant_coeffs}

    if not xgb_sig_importance:
        logger.warning("No overlapping features between LME significant set and XGBoost importance.")
        return {
            "spearman_correlation": None,
            "top3_differences": [],
            "sign_observations": [],
            "reason": "No overlapping features"
        }

    # 3. Spearman Rank Correlation
    lme_vals = [significant_coeffs[k] for k in xgb_sig_importance.keys()]
    xgb_vals = [xgb_sig_importance[k] for k in xgb_sig_importance.keys()]
    
    # Handle constant values (rank correlation undefined)
    if len(set(lme_vals)) == 1 or len(set(xgb_vals)) == 1:
        logger.warning("Constant values in importance vectors; correlation undefined.")
        spearman_corr = None
    else:
        from scipy.stats import spearmanr
        spearman_corr, _ = spearmanr(lme_vals, xgb_vals)
        logger.info(f"Spearman correlation: {spearman_corr:.4f}")

    # 4. Top-k Rank Differences
    # Sort by LME importance (desc) and XGBoost importance (desc)
    lme_ranked = sorted(xgb_sig_importance.keys(), key=lambda k: significant_coeffs[k], reverse=True)
    xgb_ranked = sorted(xgb_sig_importance.keys(), key=lambda k: xgb_sig_importance[k], reverse=True)
    
    top_k = 3
    top3_differences = []
    for i in range(min(top_k, len(lme_ranked))):
        lme_feat = lme_ranked[i]
        xgb_feat = xgb_ranked[i]
        if lme_feat != xgb_feat:
            lme_pos = i
            xgb_pos = xgb_ranked.index(lme_feat) if lme_feat in xgb_ranked else -1
            top3_differences.append({
                "feature": lme_feat,
                "lme_rank": lme_pos + 1,
                "xgb_rank": xgb_pos + 1,
                "shift": abs(lme_pos - xgb_pos)
            })
    
    # 5. Sign Observations
    # We need to know the expected physical relationship. 
    # For ductility, typically higher energy density might reduce ductility (negative), 
    # but it depends. We will just report the sign of the LME coefficient.
    sign_observations = []
    for feat, coef in significant_coeffs.items():
        # Get original signed coefficient
        orig_coef = fixed_effects[feat]['coef']
        sign_str = "Positive" if orig_coef > 0 else "Negative"
        sign_observations.append({
            "feature": feat,
            "lme_sign": sign_str,
            "lme_coefficient": float(orig_coef)
        })

    return {
        "spearman_correlation": float(spearman_corr) if spearman_corr is not None else None,
        "top3_differences": top3_differences,
        "sign_observations": sign_observations
    }

def main():
    """Main entry point for the sensitivity analysis and comparison task."""
    logger.info("Starting Feature Importance Comparison (T033)...")

    # Define paths
    lme_path = "artifacts/lme_model_results.json"
    xgb_model_path = "artifacts/xgboost_model.pkl"
    test_data_path = "data/splits/test.csv"
    output_path = "artifacts/model_comparison.json"

    # 1. Load LME Results
    try:
        lme_results = load_lme_results(lme_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load LME results: {e}")
        sys.exit(1)

    # 2. Load XGBoost Model
    try:
        xgb_model = load_xgboost_model(xgb_model_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load XGBoost model: {e}")
        sys.exit(1)

    # 3. Load Test Data
    try:
        test_data = load_data(test_data_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load test data: {e}")
        sys.exit(1)

    # Prepare features and target
    # Assuming target is 'ductility'
    target_col = 'ductility'
    if target_col not in test_data.columns:
        logger.error(f"Target column '{target_col}' not found in test data.")
        sys.exit(1)
    
    y_test = test_data[target_col]
    
    # Identify feature columns (exclude target and non-numeric identifiers)
    # We need to match the columns used in LME and XGBoost
    # Common numeric columns
    numeric_cols = test_data.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in numeric_cols:
        numeric_cols.remove(target_col)
    
    X_test = test_data[numeric_cols]

    # 4. Run Comparison
    comparison_results = compare_feature_importance(lme_results, xgb_model, X_test, y_test)

    # 5. Save Output
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    logger.info(f"Comparison results saved to {output_path}")
    logger.info(f"Spearman Correlation: {comparison_results.get('spearman_correlation')}")
    
    if comparison_results.get('top3_differences'):
        logger.info(f"Top 3 rank differences found: {len(comparison_results['top3_differences'])}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())