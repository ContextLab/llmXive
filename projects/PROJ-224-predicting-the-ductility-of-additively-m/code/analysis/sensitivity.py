"""
Sensitivity analysis module for the ductility prediction pipeline.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def load_data() -> pd.DataFrame:
    """Load filtered dataset."""
    input_path = DATA_DIR / "filtered_builds_final.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    return pd.read_csv(input_path)

def load_lme_results() -> dict:
    """Load LME results."""
    lme_path = ARTIFACTS_DIR / "lme_model_results.json"
    if not lme_path.exists():
        logger.warning(f"LME results not found: {lme_path}")
        return {}
    with open(lme_path, 'r') as f:
        return json.load(f)

def load_xgboost_model() -> tuple:
    """Load XGBoost model and metrics."""
    model_path = ARTIFACTS_DIR / "xgboost_model.pkl"
    metrics_path = ARTIFACTS_DIR / "xgboost_metrics.json"
    
    import pickle
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(metrics_path, 'r') as f:
        metrics = json.load(f)
    
    return model, metrics

def compute_partial_r2(lme_results: dict) -> float:
    """Extract partial R² from LME results."""
    return lme_results.get('partial_r2', 0.0)

def likelihood_ratio_test(lme_results: dict) -> dict:
    """Perform likelihood-ratio test (placeholder, actual test done in LME)."""
    # This is a placeholder - actual test done in lme_model.py
    return {"statistic": 0.0, "p_value": 1.0}

def run_diagnostics(df: pd.DataFrame, lme_results: dict) -> dict:
    """Run model diagnostics."""
    logger.info("Running diagnostics")
    
    partial_r2 = compute_partial_r2(lme_results)
    if partial_r2 < 0.50:
        logger.warning(f"Partial R² ({partial_r2:.4f}) < 0.50. Model explanatory power is limited.")
    
    return {"partial_r2": partial_r2}

def generate_sensitivity_report(diagnostics: dict, sensitivity_data: dict):
    """Generate sensitivity analysis report."""
    report_path = ARTIFACTS_DIR / "sensitivity_report.md"
    
    lines = [
        "# Sensitivity Analysis Report",
        "",
        "## Diagnostics",
        f"- Partial R²: {diagnostics['partial_r2']:.4f}",
        "",
        "## Alpha Sweep Results",
        ""
    ]
    
    if sensitivity_data:
        lines.append("### Standardized Coefficients by Alpha")
        for alpha, coefs in sensitivity_data.get('standardized_coefficients', {}).items():
            lines.append(f"Alpha {alpha}: {coefs}")
        lines.append("")
        lines.append("### Partial R² by Alpha")
        for alpha, r2 in sensitivity_data.get('partial_r2', {}).items():
            lines.append(f"Alpha {alpha}: {r2:.4f}")
    
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    logger.info(f"Saved sensitivity report to {report_path}")

def compare_feature_importance(xgb_importance: dict, lme_results: dict) -> dict:
    """Compare feature importance between XGBoost and LME."""
    logger.info("Comparing feature importance")
    
    if not lme_results:
        return {"spearman_correlation": None, "top3_differences": [], "sign_observations": []}
    
    # Get significant LME coefficients (p < 0.05)
    significant_features = []
    lme_coefs = {}
    for i, col in enumerate(lme_results.get('fixed_effects', [])):
        if i < len(lme_results.get('p_values', [])) and lme_results['p_values'][i] < 0.05:
            significant_features.append(col)
            lme_coefs[col] = lme_results['standardized_coefficients'].get(col, 0)
    
    # Find common features
    common_features = [f for f in significant_features if f in xgb_importance]
    
    if len(common_features) < 2:
        return {"spearman_correlation": None, "top3_differences": [], "sign_observations": []}
    
    # Compute Spearman correlation
    from scipy.stats import spearmanr
    xgb_vals = [xgb_importance[f] for f in common_features]
    lme_vals = [abs(lme_coefs[f]) for f in common_features]
    
    corr, p_val = spearmanr(xgb_vals, lme_vals)
    
    # Top 3 differences
    xgb_ranked = sorted(xgb_importance.items(), key=lambda x: x[1], reverse=True)[:3]
    lme_ranked = sorted(lme_coefs.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    
    top3_differences = []
    for i, (xgb_feat, _) in enumerate(xgb_ranked):
        if i < len(lme_ranked) and xgb_feat != lme_ranked[i][0]:
            top3_differences.append({
                "feature": xgb_feat,
                "xgb_rank": i+1,
                "lme_rank": next((j+1 for j, (f, _) in enumerate(lme_ranked) if f == xgb_feat), "N/A")
            })
    
    # Sign observations
    sign_observations = []
    for feat in common_features:
        xgb_sign = np.sign(xgb_importance[feat])
        lme_sign = np.sign(lme_coefs[feat])
        if xgb_sign != lme_sign:
            sign_observations.append(f"Sign mismatch for {feat}: XGB={xgb_sign}, LME={lme_sign}")
    
    return {
        "spearman_correlation": float(corr),
        "p_value": float(p_val),
        "top3_differences": top3_differences,
        "sign_observations": sign_observations
    }

def main():
    """Main entry point for sensitivity analysis."""
    logger.info("Starting sensitivity analysis")
    
    # Load data
    df = load_data()
    lme_results = load_lme_results()
    xgb_model, xgb_metrics = load_xgboost_model()
    
    # Run diagnostics
    diagnostics = run_diagnostics(df, lme_results)
    
    # Get XGBoost importance (placeholder - would need to recompute or load from artifact)
    xgb_importance = xgb_metrics.get('permutation_importance', {})
    
    # Compare with LME
    comparison = compare_feature_importance(xgb_importance, lme_results)
    
    # Save comparison
    comparison_path = ARTIFACTS_DIR / "model_comparison.json"
    with open(comparison_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    logger.info(f"Saved comparison to {comparison_path}")
    
    # Generate report
    sensitivity_data = {}  # Placeholder for alpha sweep data
    generate_sensitivity_report(diagnostics, sensitivity_data)
    
    return diagnostics

if __name__ == "__main__":
    main()
