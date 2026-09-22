"""
Analysis module for VIF calculations, feature importance, and model evaluation.
"""
import os
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests

from code.config import SEED, OUTLIER_SIGMA
from code.scaffold_split import scaffold_split

def filter_outliers(df: pd.DataFrame, target_col: str, sigma_threshold: float = 3.0) -> pd.DataFrame:
    """
    Filter outliers based on z-score threshold.
    
    Args:
        df: Input DataFrame
        target_col: Name of target column
        sigma_threshold: Z-score threshold for outlier removal
    
    Returns:
        Filtered DataFrame
    """
    z_scores = np.abs(stats.zscore(df[target_col].dropna()))
    filtered_df = df[z_scores <= sigma_threshold]
    logging.info(f"Filtered outliers: {len(df)} -> {len(filtered_df)} rows (threshold={sigma_threshold})")
    return filtered_df

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        X: Feature matrix (numpy array)
        feature_names: List of feature names
    
    Returns:
        Dictionary mapping feature names to VIF scores
    """
    if X.shape[1] == 0:
        return {}
    
    vif_scores = {}
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_scores[name] = float(vif)
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {name}: {e}")
            vif_scores[name] = float('inf')
    
    return vif_scores

def exclude_high_vif_features(vif_scores: Dict[str, float], threshold: float = 10.0) -> List[str]:
    """
    Exclude features with VIF > threshold.
    
    Args:
        vif_scores: Dictionary of VIF scores
        threshold: VIF threshold for exclusion
    
    Returns:
        List of features to exclude
    """
    excluded = [name for name, vif in vif_scores.items() if vif > threshold]
    if excluded:
        logging.info(f"Excluding high VIF features: {excluded}")
    return excluded

def train_and_evaluate_model(X_train: np.ndarray, y_train: np.ndarray, 
                             X_test: np.ndarray, y_test: np.ndarray, 
                             seed: int = SEED) -> Tuple[Any, Dict[str, float]]:
    """
    Train a Random Forest model and evaluate it.
    
    Args:
        X_train: Training features
        y_train: Training targets
        X_test: Test features
        y_test: Test targets
        seed: Random seed
    
    Returns:
        Tuple of (model, metrics_dict)
    """
    model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    metrics = {'r2': float(r2), 'mae': float(mae)}
    logging.info(f"Model trained: R²={r2:.4f}, MAE={mae:.4f}")
    
    return model, metrics

def run_vif_iterative_loop(X_train: np.ndarray, y_train: np.ndarray,
                           feature_names: List[str],
                           vif_threshold: float = 10.0,
                           seed: int = SEED,
                           max_iterations: int = 50) -> Dict[str, Any]:
    """
    Run iterative VIF loop to exclude high VIF features and retrain models.
    
    Args:
        X_train: Training features
        y_train: Training targets
        feature_names: List of feature names
        vif_threshold: VIF threshold for exclusion
        seed: Random seed
        max_iterations: Maximum number of iterations
    
    Returns:
        Dictionary with iteration log and final results
    """
    iteration_log = []
    current_features = feature_names.copy()
    current_X = X_train.copy()
    
    iteration = 0
    while iteration < max_iterations:
        # Calculate VIF
        vif_scores = calculate_vif(current_X, current_features)
        
        # Check for high VIF features
        high_vif = [name for name, vif in vif_scores.items() if vif > vif_threshold]
        
        if not high_vif:
            logging.info("No more high VIF features. Stopping VIF loop.")
            break
        
        # Exclude feature with highest VIF
        max_vif_feature = max(high_vif, key=lambda x: vif_scores[x])
        max_vif_value = vif_scores[max_vif_feature]
        
        logging.info(f"Iteration {iteration}: Excluding '{max_vif_feature}' (VIF={max_vif_value:.2f})")
        
        # Record iteration
        iteration_log.append({
            'iteration': iteration,
            'excluded_feature': max_vif_feature,
            'vif_scores': vif_scores,
            'remaining_features': [f for f in current_features if f != max_vif_feature]
        })
        
        # Update feature set
        current_features = [f for f in current_features if f != max_vif_feature]
        if not current_features:
            logging.critical("All features excluded. Stopping VIF loop.")
            break
        
        # Update feature matrix
        current_X = current_X[:, [i for i, f in enumerate(feature_names) if f in current_features]]
        
        # Retrain model
        model, metrics = train_and_evaluate_model(current_X, y_train, current_X, y_train, seed)
        iteration_log[-1]['r2'] = metrics['r2']
        iteration_log[-1]['mae'] = metrics['mae']
        
        iteration += 1
    
    return {
        'iterations': iteration_log,
        'final_features': current_features,
        'final_r2': iteration_log[-1]['r2'] if iteration_log else None,
        'final_mae': iteration_log[-1]['mae'] if iteration_log else None
    }

def update_model_results(results_path: str, new_results: Dict[str, Any]) -> None:
    """
    Update model results JSON file with new results.
    
    Args:
        results_path: Path to model results JSON
        new_results: New results to add
    """
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            existing = json.load(f)
        existing.update(new_results)
    else:
        existing = new_results
    
    with open(results_path, 'w') as f:
        json.dump(existing, f, indent=2)
    logging.info(f"Updated model results at {results_path}")

def calculate_feature_correlations(df: pd.DataFrame, target_col: str) -> Dict[str, Tuple[float, float]]:
    """
    Calculate Pearson correlation and p-value for each feature with target.
    
    Args:
        df: DataFrame with features and target
        target_col: Name of target column
    
    Returns:
        Dictionary mapping feature names to (correlation, p_value)
    """
    correlations = {}
    for col in df.columns:
        if col == target_col or col == 'smiles':
            continue
        
        try:
            corr, p_value = stats.pearsonr(df[col].dropna(), df[target_col].dropna())
            correlations[col] = (float(corr), float(p_value))
        except Exception as e:
            logging.warning(f"Could not calculate correlation for {col}: {e}")
            correlations[col] = (np.nan, np.nan)
    
    return correlations

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: List of p-values
    
    Returns:
        List of adjusted p-values
    """
    if not p_values:
        return []
    
    try:
        _, adjusted, _, _ = multipletests(p_values, method='fdr_bh')
        return [float(p) for p in adjusted]
    except Exception as e:
        logging.error(f"Error applying BH correction: {e}")
        return p_values

def main():
    """Main entry point for analysis module."""
    parser = argparse.ArgumentParser(description="Run analysis tasks")
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv',
                        help='Path to descriptors CSV')
    parser.add_argument('--target', type=str, default='conductivity',
                        help='Target column name')
    parser.add_argument('--outlier-sigma', type=float, default=3.0,
                        help='Sigma threshold for outlier filtering')
    
    args = parser.parse_args()
    
    setup_logging = logging.getLogger(__name__)
    setup_logging.info(f"Starting analysis with data={args.data}, target={args.target}")
    
    # Load data
    df = pd.read_csv(args.data)
    
    # Filter outliers
    df_filtered = filter_outliers(df, args.target, args.outlier_sigma)
    
    # Calculate correlations
    correlations = calculate_feature_correlations(df_filtered, args.target)
    
    # Apply BH correction
    p_values = [corr[1] for corr in correlations.values()]
    adjusted_p_values = apply_bh_correction(p_values)
    
    logging.info(f"Analysis completed. {len(correlations)} features analyzed.")

if __name__ == '__main__':
    main()
