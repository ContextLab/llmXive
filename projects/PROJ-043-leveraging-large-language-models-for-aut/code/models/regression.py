import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from utils.logging import get_logger
import statsmodels.api as sm
import json
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

logger = get_logger(__name__)

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factors (VIF) for all predictors.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: List of feature names corresponding to columns in X
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    vif_data = {}
    # Add intercept for calculation but exclude from VIF
    X_with_intercept = sm.add_constant(X)
    
    for i in range(X.shape[1]):
        # Exclude the current feature and include all others + intercept
        independent = np.column_stack([X_with_intercept[:, 0], X_with_intercept[:, i+1:] if i < X.shape[1]-1 else X_with_intercept[:, 1:]])
        if independent.shape[1] == 0:
            vif_data[feature_names[i]] = 0.0
            continue
            
        try:
            model = sm.OLS(X[:, i], independent).fit()
            vif = 1.0 / (1.0 - model.rsquared)
            vif_data[feature_names[i]] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {feature_names[i]}: {e}")
            vif_data[feature_names[i]] = float('inf')
            
    return vif_data

def vif_filtering(X: np.ndarray, y: np.ndarray, feature_names: List[str], threshold: float = 5.0) -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Iteratively drop predictors with VIF > threshold until all remaining have VIF <= threshold.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of original feature names
        threshold: VIF threshold for removal (default 5.0)
        
    Returns:
        Tuple of (filtered_X, filtered_feature_names, removed_feature_names)
    """
    current_X = X.copy()
    current_names = feature_names.copy()
    removed_names = []
    
    while True:
        vif_data = calculate_vif(current_X, current_names)
        max_vif_feature = max(vif_data, key=vif_data.get)
        max_vif = vif_data[max_vif_feature]
        
        if max_vif <= threshold:
            logger.info(f"VIF filtering complete. All features have VIF <= {threshold}.")
            break
            
        logger.info(f"Removing '{max_vif_feature}' with VIF = {max_vif:.2f}")
        idx = current_names.index(max_vif_feature)
        
        # Remove from X and names
        current_X = np.delete(current_X, idx, axis=1)
        current_names.pop(idx)
        removed_names.append(max_vif_feature)
        
        if len(current_names) == 0:
            logger.error("All features removed due to high VIF. Cannot fit model.")
            break
            
    return current_X, current_names, removed_names

def fit_ols_model(X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> Dict[str, Any]:
    """
    Fit a standard Multiple Linear Regression (OLS) model.
    
    Args:
        X: Feature matrix (filtered)
        y: Target vector
        feature_names: List of feature names
        
    Returns:
        Dictionary containing model results: coefficients, p-values, adjusted_r2
    """
    if X.shape[0] == 0:
        raise ValueError("Cannot fit model with no samples.")
    if X.shape[1] == 0:
        raise ValueError("Cannot fit model with no features.")
        
    X_with_const = sm.add_constant(X)
    
    try:
        model = sm.OLS(y, X_with_const).fit()
    except Exception as e:
        logger.error(f"OLS fitting failed: {e}")
        raise
        
    results = {
        "coefficients": {},
        "p_values": {},
        "adjusted_r2": float(model.rsquared_adj),
        "r2": float(model.rsquared),
        "f_statistic": float(model.fvalue),
        "f_p_value": float(model.f_pvalue),
        "n_obs": int(model.nobs),
        "n_features": len(feature_names)
    }
    
    # Map coefficients and p-values to feature names
    # Index 0 is constant, 1..n are features
    for i, name in enumerate(feature_names):
        results["coefficients"][name] = float(model.params[i+1])
        results["p_values"][name] = float(model.pvalues[i+1])
        
    results["intercept"] = float(model.params[0])
    results["intercept_p_value"] = float(model.pvalues[0])
    
    logger.info(f"OLS Model fitted. Adjusted R² = {results['adjusted_r2']:.4f}")
    return results

def run_regression_analysis(
    data: List[Dict[str, Any]], 
    target_delta: str, 
    feature_candidates: List[str],
    vif_threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Run full regression analysis pipeline: VIF filtering, OLS fitting, and cross-validation.
    
    Args:
        data: List of samples with features and target
        target_delta: Name of the target variable (e.g., 'complexity_delta')
        feature_candidates: List of candidate predictor names
        vif_threshold: VIF threshold for filtering
        
    Returns:
        Dictionary containing full analysis results
    """
    # Extract features and target
    X_list = []
    y_list = []
    valid_indices = []
    
    for i, sample in enumerate(data):
        if target_delta not in sample:
            logger.warning(f"Sample {i} missing target '{target_delta}', skipping.")
            continue
            
        y_val = sample[target_delta]
        if y_val is None or (isinstance(y_val, float) and np.isnan(y_val)):
            continue
            
        row = []
        valid = True
        for feat in feature_candidates:
            val = sample.get(feat)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                valid = False
                break
            row.append(float(val))
            
        if valid:
            X_list.append(row)
            y_list.append(float(y_val))
            valid_indices.append(i)
            
    if len(X_list) == 0:
        raise ValueError("No valid samples found for regression analysis.")
        
    X = np.array(X_list)
    y = np.array(y_list)
    
    logger.info(f"Prepared {len(y)} samples with {len(feature_candidates)} features.")
    
    # Step 1: VIF Filtering
    X_filtered, filtered_names, removed_names = vif_filtering(X, y, feature_candidates, vif_threshold)
    
    if len(filtered_names) == 0:
        raise ValueError("VIF filtering removed all features. Cannot proceed.")
        
    logger.info(f"Features after VIF filtering: {filtered_names}")
    if removed_names:
        logger.info(f"Removed features: {removed_names}")
        
    # Step 2: Fit OLS on full filtered data (for baseline comparison)
    full_model_results = fit_ols_model(X_filtered, y, filtered_names)
    
    # Step 3: K-Fold Cross-Validation to get mean coefficients
    n_folds = min(5, len(y))  # Use 5 folds or fewer if data is small
    if n_folds < 2:
        logger.warning("Insufficient data for cross-validation. Skipping CV step.")
        mean_coefficients = full_model_results["coefficients"]
        mean_adj_r2 = full_model_results["adjusted_r2"]
    else:
        logger.info(f"Performing {n_folds}-fold cross-validation...")
        kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
        
        all_coefficients = {name: [] for name in filtered_names}
        all_adj_r2 = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X_filtered)):
            X_train, X_test = X_filtered[train_idx], X_filtered[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            fold_results = fit_ols_model(X_train, y_train, filtered_names)
            
            # Store coefficients
            for name in filtered_names:
                all_coefficients[name].append(fold_results["coefficients"][name])
            all_adj_r2.append(fold_results["adjusted_r2"])
            
            # Calculate fold R2 on test set
            X_test_const = sm.add_constant(X_test)
            pred = fold_results["intercept"] + sum(
                fold_results["coefficients"][name] * X_test[:, i] 
                for i, name in enumerate(filtered_names)
            )
            fold_r2 = r2_score(y_test, pred)
            logger.debug(f"Fold {fold_idx+1} R²: {fold_r2:.4f}")
            
        # Compute means
        mean_coefficients = {name: np.mean(vals) for name, vals in all_coefficients.items()}
        mean_adj_r2 = float(np.mean(all_adj_r2))
        std_adj_r2 = float(np.std(all_adj_r2))
        
        logger.info(f"Cross-Validation Mean Adjusted R²: {mean_adj_r2:.4f} (±{std_adj_r2:.4f})")
        
    return {
        "vif_threshold": vif_threshold,
        "features_used": filtered_names,
        "features_removed": removed_names,
        "n_samples": len(y),
        "n_features_final": len(filtered_names),
        "full_model": full_model_results,
        "cross_validation": {
            "n_folds": n_folds,
            "mean_coefficients": mean_coefficients,
            "mean_adjusted_r2": mean_adj_r2
        } if n_folds >= 2 else None
    }

def main():
    """Main entry point for regression analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run regression analysis on refactoring data.")
    parser.add_argument("--input", type=str, default="data/processed/refactoring_results.json",
                      help="Path to input JSON with refactoring results")
    parser.add_argument("--output", type=str, default="data/results/model_summary.json",
                      help="Path to output summary JSON")
    parser.add_argument("--target", type=str, default="complexity_delta",
                      help="Target variable name for regression")
    parser.add_argument("--vif-threshold", type=float, default=5.0,
                      help="VIF threshold for feature filtering")
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    try:
        with open(args.input, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        raise
        
    # Define candidate features based on project context
    # These are the structural predictors computed in US1
    candidate_features = [
        "loc", 
        "nesting_depth", 
        "param_count", 
        "pep8_violations", 
        "maintainability_index"
    ]
    
    logger.info(f"Running regression analysis with target '{args.target}'")
    logger.info(f"Candidate features: {candidate_features}")
    
    results = run_regression_analysis(
        data=data,
        target_delta=args.target,
        feature_candidates=candidate_features,
        vif_threshold=args.vif_threshold
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Model summary saved to {output_path}")
    return results

if __name__ == "__main__":
    main()