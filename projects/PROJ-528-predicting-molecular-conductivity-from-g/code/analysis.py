import os
import json
import logging
import argparse
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from statsmodels.stats.outlier_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.inspection import permutation_importance
from scipy.stats import pearsonr, kruskal

from code.config import SEED, OUTLIER_SIGMA, VIF_THRESHOLD, TARGET_VAR, DATA_PATH
from code.logging_config import setup_logging
from code.scaffold_split import scaffold_split
from code.data_loader import load_processed_data, apply_log_transformation

logger = setup_logging(__name__)

def calculate_vif(features: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    """
    if features.shape[0] < 2 or features.shape[1] == 0:
        return {name: np.inf for name in feature_names}
    
    # Add constant for intercept
    try:
        vif_data = []
        for i in range(features.shape[1]):
            y = features[:, i]
            X = np.hstack([np.ones((features.shape[0], 1)), np.delete(features, i, axis=1)])
            if X.shape[1] < 2:
                vif = np.inf
            else:
                try:
                    vif = variance_inflation_factor(X, 1) # 1 is index of y in X (since 0 is intercept)
                    # Actually, variance_inflation_factor expects X without intercept usually
                    # Let's use the standard approach: regress feature i against all others
                    X_others = np.delete(features, i, axis=1)
                    if X_others.shape[1] == 0:
                        vif = np.inf
                    else:
                        # Add constant
                        X_others_const = np.hstack([np.ones((X_others.shape[0], 1)), X_others])
                        vif = variance_inflation_factor(X_others_const, 1)
                except Exception:
                    vif = np.inf
            vif_data.append((feature_names[i], vif))
        return dict(vif_data)
    except Exception as e:
        logger.error(f"Error calculating VIF: {e}")
        return {name: np.inf for name in feature_names}

def filter_outliers(df: pd.DataFrame, target_col: str, sigma_threshold: float) -> pd.DataFrame:
    """
    Filter outliers based on z-score of target variable.
    """
    if target_col not in df.columns:
        logger.error(f"Target column {target_col} not found in dataframe")
        return df
    
    z_scores = np.abs((df[target_col] - df[target_col].mean()) / df[target_col].std())
    filtered_df = df[z_scores <= sigma_threshold]
    dropped_count = len(df) - len(filtered_df)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows due to outlier threshold {sigma_threshold}")
    return filtered_df

def run_sensitivity_analysis(df: pd.DataFrame, target_col: str, thresholds: List[float]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by varying outlier threshold.
    """
    results = {
        "thresholds": [],
        "r2_scores": [],
        "variance_metrics": []
    }
    
    # Prepare data
    feature_cols = [c for c in df.columns if c not in ['smiles', 'status', target_col, f'log_{target_col}']]
    if not feature_cols:
        logger.error("No feature columns found")
        return results
    
    X = df[feature_cols].values
    y = df[f'log_{target_col}'].values if f'log_{target_col}' in df.columns else df[target_col].values
    
    # Split once
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
    except Exception as e:
        logger.error(f"Train/test split failed: {e}")
        return results

    for thresh in thresholds:
        # Filter outliers
        # We need to apply filter on original df based on target_col, then re-split
        # This is computationally expensive but necessary for correct sensitivity analysis
        filtered_df = filter_outliers(df, f'log_{target_col}', thresh)
        
        if len(filtered_df) < 10:
            logger.warning(f"Too few samples after filtering with threshold {thresh}, skipping")
            continue
        
        X_f = filtered_df[feature_cols].values
        y_f = filtered_df[f'log_{target_col}'].values
        
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(X_f, y_f, test_size=0.2, random_state=SEED)
            model = RandomForestRegressor(n_estimators=100, random_state=SEED)
            model.fit(X_tr, y_tr)
            scores = cross_val_score(model, X_tr, y_tr, cv=5, scoring='r2')
            results["thresholds"].append(thresh)
            results["r2_scores"].append(float(np.mean(scores)))
            results["variance_metrics"].append(float(np.std(scores)))
        except Exception as e:
            logger.warning(f"Training failed for threshold {thresh}: {e}")
            continue

    if len(results["thresholds"]) > 1:
        # Kruskal-Wallis test
        try:
            stat, p_val = kruskal(*results["r2_scores"])
            results["kruskal_statistic"] = float(stat)
            results["p_value"] = float(p_val)
        except Exception as e:
            logger.warning(f"Kruskal-Wallis test failed: {e}")
            results["kruskal_statistic"] = None
            results["p_value"] = None
    else:
        results["kruskal_statistic"] = None
        results["p_value"] = None

    return results

def exclude_high_vif_features(feature_names: List[str], vif_scores: Dict[str, float], threshold: float) -> List[str]:
    """
    Return list of features with VIF > threshold.
    """
    return [name for name in feature_names if vif_scores.get(name, np.inf) > threshold]

def run_vif_iterative_retrain(df: pd.DataFrame, target_col: str, vif_threshold: float = 10.0) -> Tuple[Dict[str, float], List[str], List[Dict]]:
    """
    Iteratively remove high VIF features and retrain, recording metrics.
    """
    feature_cols = [c for c in df.columns if c not in ['smiles', 'status', target_col, f'log_{target_col}']]
    if not feature_cols:
        return {}, [], []
    
    current_features = list(feature_cols)
    iteration_log = []
    excluded_features = []
    
    while True:
        X = df[current_features].values
        y = df[f'log_{target_col}'].values if f'log_{target_col}' in df.columns else df[target_col].values
        
        if X.shape[1] == 0:
            logger.critical("Feature set became empty during VIF iteration. Halting.")
            break
        
        vif_scores = calculate_vif(X, current_features)
        high_vif = exclude_high_vif_features(current_features, vif_scores, vif_threshold)
        
        if not high_vif:
            break
        
        # Remove the feature with highest VIF
        max_vif_feature = max(high_vif, key=lambda x: vif_scores[x])
        excluded_features.append(max_vif_feature)
        current_features.remove(max_vif_feature)
        
        # Retrain and record
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)
            model = RandomForestRegressor(n_estimators=100, random_state=SEED)
            model.fit(X_tr, y_tr)
            r2 = model.score(X_te, y_te)
            iteration_log.append({
                "removed_feature": max_vif_feature,
                "remaining_features": current_features,
                "r2": float(r2)
            })
        except Exception as e:
            logger.error(f"Error during VIF iteration: {e}")
            break
    
    final_vif = calculate_vif(df[current_features].values, current_features)
    return final_vif, excluded_features, iteration_log

def apply_bh_correction(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    Input: dictionary mapping feature names to p-values.
    Output: dictionary mapping feature names to adjusted p-values.
    """
    if not p_values:
        return {}
    
    features = list(p_values.keys())
    p_vals = list(p_values.values())
    
    # Filter out non-finite values for calculation, but keep track
    valid_indices = [i for i, p in enumerate(p_vals) if np.isfinite(p)]
    if not valid_indices:
        return {k: np.nan for k in features}
    
    valid_p_vals = [p_vals[i] for i in valid_indices]
    valid_features = [features[i] for i in valid_indices]
    
    try:
        # multipletests returns (reject, p_corrected, p_sidak, p_holm)
        # We want p_corrected (FDR corrected)
        _, p_corrected, _, _ = multipletests(valid_p_vals, method='fdr_bh')
        
        # Map back to full dictionary
        result = {k: np.nan for k in features}
        for i, feature in enumerate(valid_features):
            result[feature] = float(p_corrected[i])
        
        return result
    except Exception as e:
        logger.error(f"Benjamini-Hochberg correction failed: {e}")
        return {k: np.nan for k in features}

def main():
    parser = argparse.ArgumentParser(description="Analysis pipeline")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output directory")
    parser.add_argument("--thresholds", type=float, nargs='+', default=[2.0, 3.0, 4.0], help="Sigma thresholds for sensitivity analysis")
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)
    
    if df is None or df.empty:
        logger.error("Failed to load data")
        return
    
    # Ensure log target exists
    if TARGET_VAR in df.columns and f'log_{TARGET_VAR}' not in df.columns:
        df = apply_log_transformation(df, TARGET_VAR)
    
    # Run VIF iterative retrain
    logger.info("Running VIF iterative retrain...")
    final_vif, excluded, iter_log = run_vif_iterative_retrain(df, TARGET_VAR, VIF_THRESHOLD)
    
    # Save VIF analysis
    os.makedirs(args.output, exist_ok=True)
    vif_path = os.path.join(args.output, "vif_analysis.json")
    with open(vif_path, "w") as f:
        json.dump({"final_vif": final_vif, "excluded_features": excluded}, f, indent=2)
    logger.info(f"Saved VIF analysis to {vif_path}")
    
    # Save iteration log
    iter_path = os.path.join(args.output, "vif_iteration_log.json")
    with open(iter_path, "w") as f:
        json.dump(iter_log, f, indent=2)
    logger.info(f"Saved VIF iteration log to {iter_path}")
    
    # Calculate correlations
    feature_cols = [c for c in df.columns if c not in ['smiles', 'status', TARGET_VAR, f'log_{TARGET_VAR}']]
    if not feature_cols:
        logger.warning("No features left for correlation analysis")
        return
    
    correlations = {}
    y = df[f'log_{TARGET_VAR}'].values
    for feat in feature_cols:
        x = df[feat].values
        if np.std(x) == 0 or np.std(y) == 0:
            correlations[feat] = (0.0, 1.0)
            continue
        try:
            r, p = pearsonr(x, y)
            correlations[feat] = (float(r), float(p))
        except Exception:
            correlations[feat] = (np.nan, np.nan)
    
    # Extract raw p-values for BH correction
    p_values = {k: v[1] for k, v in correlations.items()}
    
    # Apply BH correction
    logger.info("Applying Benjamini-Hochberg FDR correction...")
    adjusted_p_values = apply_bh_correction(p_values)
    
    # Update correlations with adjusted p-values
    final_correlations = {k: {"r": v[0], "p_raw": v[1], "p_adj": adjusted_p_values.get(k, np.nan)} for k, v in correlations.items()}
    
    # Save correlation results
    corr_path = os.path.join(args.output, "correlation_results.json")
    with open(corr_path, "w") as f:
        json.dump(final_correlations, f, indent=2)
    logger.info(f"Saved correlation results to {corr_path}")
    
    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    sens_results = run_sensitivity_analysis(df, TARGET_VAR, args.thresholds)
    sens_path = os.path.join(args.output, "sensitivity_analysis.json")
    with open(sens_path, "w") as f:
        json.dump(sens_results, f, indent=2)
    logger.info(f"Saved sensitivity analysis to {sens_path}")

if __name__ == "__main__":
    main()