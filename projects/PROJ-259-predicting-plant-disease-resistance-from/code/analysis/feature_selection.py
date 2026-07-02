import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import warnings

from config import get_reports_path
from utils.logging import get_logger
from utils.stats import benjamini_hochberg

logger = get_logger(__name__)

def load_split_data(split_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load training data from the split directory.
    Returns X_train, y_train, and feature names if available.
    """
    X_path = Path(split_path) / "X_train.csv"
    y_path = Path(split_path) / "y_train.csv"
    
    if not X_path.exists() or not y_path.exists():
        raise FileNotFoundError(f"Split data not found at {split_path}")
    
    X = pd.read_csv(X_path, index_col=0)
    y = pd.read_csv(y_path, index_col=0)
    
    # Ensure y is a Series
    if isinstance(y, pd.DataFrame):
        y = y.iloc[:, 0]
        
    return X, y, X.columns

def run_lasso_selection(X: pd.DataFrame, y: pd.Series, alpha: float = 0.01) -> Tuple[List[str], np.ndarray]:
    """
    Run LASSO regression for feature selection and return selected features.
    Also returns the coefficients for effect size calculation.
    """
    from sklearn.linear_model import LassoCV
    
    # Standardize features for LASSO
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Use LassoCV for automated alpha selection, or fixed alpha if preferred
    # Here we use a fixed alpha for consistency with sensitivity sweep
    lasso = LassoCV(alphas=[alpha], cv=5, random_state=42, max_iter=10000)
    lasso.fit(X_scaled, y)
    
    coefficients = lasso.coef_
    selected_mask = coefficients != 0
    selected_features = X.columns[selected_mask].tolist()
    
    logger.info(f"LASSO selected {len(selected_features)} features with alpha={alpha}")
    
    return selected_features, coefficients

def run_rf_selection(X: pd.DataFrame, y: pd.Series, n_estimators: int = 100) -> Tuple[List[str], np.ndarray]:
    """
    Run Random Forest for feature selection and return selected features.
    Also returns feature importances as effect size proxy.
    """
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import cross_val_score
    
    # Determine problem type
    if y.nunique() <= 5:
        # Likely classification
        rf = RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    else:
        # Likely regression
        rf = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    
    rf.fit(X, y)
    importances = rf.feature_importances_
    
    # Select features with importance > 0 (or a threshold)
    # For this task, we'll select top 20% or all with non-zero importance
    threshold = np.percentile(importances, 80) if len(importances) > 0 else 0
    selected_mask = importances > threshold
    selected_features = X.columns[selected_mask].tolist()
    
    logger.info(f"RF selected {len(selected_features)} features with threshold={threshold}")
    
    return selected_features, importances

def run_sensitivity_sweep(X: pd.DataFrame, y: pd.Series, thresholds: List[float] = [0.01, 0.05, 0.1]) -> pd.DataFrame:
    """
    Run feature selection across multiple thresholds and calculate selection frequency.
    Returns a DataFrame with feature_id, threshold, and frequency.
    """
    results = []
    
    for threshold in thresholds:
        # Run LASSO with current threshold as alpha
        selected_features, coefficients = run_lasso_selection(X, y, alpha=threshold)
        
        # Count selection frequency (for a single run, frequency is 1 if selected, 0 otherwise)
        # In a real sweep with multiple iterations, this would aggregate across runs
        for feature in X.columns:
            freq = 1.0 if feature in selected_features else 0.0
            results.append({
                'feature_id': feature,
                'threshold': threshold,
                'frequency': freq,
                'effect_size': coefficients[list(X.columns).index(feature)] if feature in selected_features else 0.0
            })
    
    return pd.DataFrame(results)

def save_selection_frequency(df: pd.DataFrame, output_path: str):
    """
    Save the selection frequency DataFrame to CSV.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved selection frequency to {output_path}")

def calculate_effect_sizes(X: pd.DataFrame, y: pd.Series, selected_features: List[str], method: str = "lasso") -> Dict[str, float]:
    """
    Calculate effect-size coefficients for selected features.
    Returns a dictionary mapping feature_id to effect size.
    """
    if method == "lasso":
        # Use LASSO coefficients
        _, coefficients = run_lasso_selection(X, y)
        effect_sizes = {
            feat: float(coefficients[list(X.columns).index(feat)]) 
            for feat in selected_features if feat in X.columns
        }
    elif method == "rf":
        # Use RF importances
        _, importances = run_rf_selection(X, y)
        effect_sizes = {
            feat: float(importances[list(X.columns).index(feat)]) 
            for feat in selected_features if feat in X.columns
        }
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return effect_sizes

def run_feature_selection_pipeline(
    split_path: str, 
    output_path: str,
    thresholds: List[float] = [0.01, 0.05, 0.1],
    method: str = "lasso"
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Run the full feature selection pipeline:
    1. Load data
    2. Run sensitivity sweep
    3. Calculate effect sizes for selected features
    4. Save results
    
    Returns the selection frequency DataFrame and effect sizes dictionary.
    """
    logger.info(f"Starting feature selection pipeline for {split_path}")
    
    # Load data
    X, y, feature_names = load_split_data(split_path)
    logger.info(f"Loaded {X.shape[0]} samples and {X.shape[1]} features")
    
    # Run sensitivity sweep
    freq_df = run_sensitivity_sweep(X, y, thresholds)
    
    # Identify top features based on frequency (e.g., selected in at least 1 threshold)
    top_features = freq_df[freq_df['frequency'] > 0]['feature_id'].unique().tolist()
    logger.info(f"Identified {len(top_features)} top features across thresholds")
    
    # Calculate effect sizes for top features
    effect_sizes = calculate_effect_sizes(X, y, top_features, method=method)
    
    # Save selection frequency
    save_selection_frequency(freq_df, output_path)
    
    # Also save effect sizes to a separate file for downstream use
    effect_size_path = str(Path(output_path).parent / "effect_sizes.csv")
    effect_size_df = pd.DataFrame([
        {'feature_id': feat, 'effect_size': size} 
        for feat, size in effect_sizes.items()
    ])
    effect_size_df.to_csv(effect_size_df, index=False)
    logger.info(f"Saved effect sizes to {effect_size_path}")
    
    return freq_df, effect_sizes

def main():
    """
    Main entry point for feature selection script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run feature selection with effect size calculation")
    parser.add_argument("--split-path", type=str, default="data/processed/split", help="Path to split data")
    parser.add_argument("--output", type=str, default="artifacts/reports/selection_frequency.csv", help="Output path for selection frequency")
    parser.add_argument("--thresholds", type=str, default="0.01,0.05,0.1", help="Comma-separated list of thresholds")
    parser.add_argument("--method", type=str, default="lasso", choices=["lasso", "rf"], help="Feature selection method")
    
    args = parser.parse_args()
    
    thresholds = [float(t) for t in args.thresholds.split(",")]
    
    freq_df, effect_sizes = run_feature_selection_pipeline(
        split_path=args.split_path,
        output_path=args.output,
        thresholds=thresholds,
        method=args.method
    )
    
    logger.info("Feature selection pipeline completed successfully")
    return freq_df, effect_sizes

if __name__ == "__main__":
    main()