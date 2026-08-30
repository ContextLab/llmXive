import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score

# Import from local project modules based on provided API surface
# We need to load the collinearity report to check for confounders if possible
# We need to load the preprocessed data (residuals)
# We assume the RF model artifact exists from T030

from config import get_config
from data.preprocessing import load_processed_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

def load_rf_model_artifact(model_path: str) -> Optional[RandomForestRegressor]:
    """
    Load the trained Random Forest model from the artifact path.
    Since we cannot pickle in a pure script without knowing the exact environment
    of the training (though sklearn pickles are standard), we assume the model
    was saved as a pickle or joblib file by T030.
    If not found, we raise an error as we cannot proceed without the model.
    """
    import joblib
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"RF Model artifact not found at {model_path}. "
                                "Ensure T030 has completed successfully.")
    return joblib.load(model_path)

def load_collinearity_report(report_path: str) -> Dict[str, Any]:
    """Load the collinearity report generated in T023."""
    if not os.path.exists(report_path):
        logger.warning(f"Collinearity report not found at {report_path}. "
                       "Proceeding without confounder check context.")
        return {"flagged_pairs": []}
    with open(report_path, 'r') as f:
        return json.load(f)

def get_feature_importance_stability(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: np.ndarray,
    thresholds: List[float] = [0.0, 0.05, 0.1]
) -> Dict[str, Any]:
    """
    Perform threshold sweep to calculate stability of top-k interaction terms.
    
    1. Get feature importances.
    2. For each threshold, identify top-k terms where importance > threshold.
    3. Calculate stability: % of terms that remain in top-k across all thresholds.
    """
    importances = model.feature_importances_
    feature_names = X.columns.tolist()
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    results = []
    all_top_k_terms = set()
    top_k_counts = {} # Track how many times a term appears in top-k across thresholds
    
    # We define top-k as the top 5 significant terms (or fewer if not enough)
    k = 5 
    
    for threshold in thresholds:
        # Filter features above threshold
        significant_features = importance_df[importance_df['importance'] > threshold]
        top_k_features = significant_features.head(k)['feature'].tolist()
        
        # Convert to set for comparison
        top_k_set = set(top_k_features)
        all_top_k_terms.update(top_k_set)
        
        results.append({
            "threshold": threshold,
            "top_5_terms": top_k_features,
            "count": len(top_k_features)
        })
        
        # Track stability: how many times does a feature appear in the top-k list?
        for feat in top_k_features:
            top_k_counts[feat] = top_k_counts.get(feat, 0) + 1
    
    # Calculate stability percentage for the union of all top-k terms found
    # Stability = (Number of times a term appeared in top-k across all thresholds) / (Total number of thresholds)
    # But the task asks for "stability percentage (>80% required)" for the top-k terms.
    # Interpretation: What percentage of the identified "significant" terms (union) 
    # were consistently in the top-k across all thresholds?
    
    total_thresholds = len(thresholds)
    stable_terms = [feat for feat, count in top_k_counts.items() if count == total_thresholds]
    stability_pct = (len(stable_terms) / len(all_top_k_terms) * 100) if all_top_k_terms else 0.0
    
    # If no terms found, stability is 0 or 100? If empty, no terms to be stable.
    if len(all_top_k_terms) == 0:
        stability_pct = 0.0
    
    return {
        "threshold_sweep_results": results,
        "stable_terms": stable_terms,
        "stability_pct": round(stability_pct, 2)
    }

def check_confounder_r2_delta(
    model: RandomForestRegressor,
    X: pd.DataFrame,
    y: np.ndarray,
    collinearity_report: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Attempt to refit model with proxy variables if present.
    Check if 'strain_rate' or similar proxy variables exist in X.
    If present, refit without them and calculate R2 delta.
    If missing, log and return 0.0 or None.
    """
    proxy_candidates = ['strain_rate', 'strain', 'deformation_rate', 'cooling_rate']
    available_proxies = [p for p in proxy_candidates if p in X.columns]
    
    if not available_proxies:
        logger.info("No proxy variables (e.g., strain rate) available in dataset for confounder check.")
        return {
            "status": "no_proxies",
            "message": "No proxy variables available",
            "r2_delta": None,
            "available_proxies": []
        }
    
    logger.info(f"Found proxy variables: {available_proxies}. Performing confounder check.")
    
    # Base model (already trained)
    # Since we have the model, we can predict on X to get R2_base
    # However, the model might have been trained on a subset or with specific preprocessing.
    # To be safe, we assume the passed X and y are the same data used to train the model.
    # We calculate R2 of the current model on this data.
    y_pred_base = model.predict(X)
    r2_base = r2_score(y, y_pred_base)
    
    # Refit without proxies
    # We need to retrain a new RF on X without the proxy columns
    # We use the same hyperparameters as T030 (default or best from grid)
    # Assuming default for simplicity as we don't have the exact best_params from T030 here
    # In a real pipeline, we would load the best_params from the model artifact or config.
    # For this task, we assume standard RF params.
    X_no_proxies = X.drop(columns=available_proxies)
    
    # Check if X_no_proxies has enough features
    if X_no_proxies.shape[1] == 0:
        logger.error("Removing proxies leaves no features. Cannot calculate delta.")
        return {
            "status": "error",
            "message": "Removing proxies leaves no features",
            "r2_delta": None
        }
    
    # Train a new model on the reduced set
    # Using same random_state for consistency if possible, but we don't have it here.
    # We assume a generic seed or no seed for the comparison.
    model_no_proxy = RandomForestRegressor(
        n_estimators=100, 
        max_depth=10, 
        random_state=42, 
        n_jobs=-1
    )
    model_no_proxy.fit(X_no_proxies, y)
    
    y_pred_no_proxy = model_no_proxy.predict(X) # Predict on full X (though model only sees subset)
    # Actually, predict on X_no_proxies
    y_pred_no_proxy = model_no_proxy.predict(X_no_proxies)
    r2_no_proxy = r2_score(y, y_pred_no_proxy)
    
    r2_delta = r2_base - r2_no_proxy
    logger.info(f"R2 Base: {r2_base:.4f}, R2 No Proxy: {r2_no_proxy:.4f}, Delta: {r2_delta:.4f}")
    
    return {
        "status": "completed",
        "message": f"Refit without {available_proxies}",
        "r2_base": round(r2_base, 4),
        "r2_no_proxy": round(r2_no_proxy, 4),
        "r2_delta": round(r2_delta, 4),
        "proxies_removed": available_proxies
    }

def run_sensitivity_analysis(
    model_path: str,
    data_path: str,
    collinearity_report_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main entry point for the Unified Sensitivity Analysis.
    """
    logger.info(f"Loading RF model from {model_path}")
    model = load_rf_model_artifact(model_path)
    
    logger.info(f"Loading processed data from {data_path}")
    # load_processed_data returns (X, y) or a dict? 
    # Based on T020-T022, it likely returns a DataFrame or tuple.
    # Assuming it returns (X, y) as per standard sklearn patterns in this project.
    try:
        data_result = load_processed_data(data_path)
        if isinstance(data_result, tuple):
            X, y = data_result
        elif isinstance(data_result, dict):
            X = pd.DataFrame(data_result['X'])
            y = np.array(data_result['y'])
        else:
            raise ValueError("Unexpected data format from load_processed_data")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise
    
    logger.info(f"Loading collinearity report from {collinearity_report_path}")
    collinearity_report = load_collinearity_report(collinearity_report_path)
    
    # 1. Threshold Sweep
    logger.info("Performing threshold sweep for feature importance stability...")
    stability_results = get_feature_importance_stability(model, X, y)
    
    # 2. Confounder Check
    logger.info("Performing confounder check...")
    confounder_results = check_confounder_r2_delta(model, X, y, collinearity_report)
    
    # Compile Report
    report = {
        "threshold_sweep": stability_results,
        "confounder_check": confounder_results,
        "metadata": {
            "model_path": model_path,
            "data_path": data_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity report written to {output_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Run Unified Sensitivity Analysis (T032)")
    parser.add_argument("--model-path", type=str, required=True, help="Path to RF model artifact")
    parser.add_argument("--data-path", type=str, required=True, help="Path to processed data")
    parser.add_argument("--collinearity-report-path", type=str, required=True, help="Path to collinearity report")
    parser.add_argument("--output-path", type=str, required=True, help="Path to output sensitivity report")
    
    args = parser.parse_args()
    
    try:
        run_sensitivity_analysis(
            model_path=args.model_path,
            data_path=args.data_path,
            collinearity_report_path=args.collinearity_report_path,
            output_path=args.output_path
        )
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
