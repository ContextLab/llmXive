import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pickle

from config import get_path, load_config
from utils.logging import log_pipeline_step, setup_logger

# Configure logger for this module
logger = setup_logger("feature_selection")

def load_split_data(split_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Load training data from the split directory.
    
    Returns:
        Tuple of (X_train, y_train, X_val, y_val)
    """
    if split_dir is None:
        split_dir = get_path("data", "processed", "split")
    
    X_train_path = split_dir / "X_train.csv"
    y_train_path = split_dir / "y_train.csv"
    X_val_path = split_dir / "X_val.csv"
    y_val_path = split_dir / "y_val.csv"
    
    if not all(p.exists() for p in [X_train_path, y_train_path, X_val_path, y_val_path]):
        raise FileNotFoundError(f"Split data files not found in {split_dir}")
    
    X_train = pd.read_csv(X_train_path, index_col=0)
    y_train = pd.read_csv(y_train_path, index_col=0).squeeze()
    X_val = pd.read_csv(X_val_path, index_col=0)
    y_val = pd.read_csv(y_val_path, index_col=0).squeeze()
    
    logger.info(f"Loaded training data: X_train shape {X_train.shape}, y_train shape {y_train.shape}")
    logger.info(f"Loaded validation data: X_val shape {X_val.shape}, y_val shape {y_val.shape}")
    
    return X_train, y_train, X_val, y_val

def run_lasso_selection(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    X_val: pd.DataFrame, 
    y_val: pd.Series,
    alpha: float = 0.01,
    max_iter: int = 10000
) -> Tuple[List[str], Dict[str, float], float]:
    """
    Run LASSO feature selection and return selected features, coefficients, and validation score.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        alpha: L1 penalty strength
        max_iter: Maximum iterations for solver
        
    Returns:
        Tuple of (selected_feature_names, coefficients_dict, val_score)
    """
    from sklearn.linear_model import Lasso
    
    # Fit LASSO model
    lasso = Lasso(alpha=alpha, max_iter=max_iter, random_state=42)
    lasso.fit(X_train, y_train)
    
    # Extract coefficients
    coef_dict = dict(zip(X_train.columns, lasso.coef_))
    
    # Select features with non-zero coefficients
    selected_features = [feat for feat, coef in coef_dict.items() if coef != 0]
    
    # Calculate validation score
    val_score = lasso.score(X_val, y_val)
    
    logger.info(f"LASSO selected {len(selected_features)} features with alpha={alpha}")
    
    return selected_features, coef_dict, val_score

def run_rf_selection(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    X_val: pd.DataFrame, 
    y_val: pd.Series,
    n_estimators: int = 100,
    threshold: float = 0.01
) -> Tuple[List[str], Dict[str, float], float]:
    """
    Run Random Forest feature selection and return selected features, importances, and validation score.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        n_estimators: Number of trees
        threshold: Minimum importance threshold
        
    Returns:
        Tuple of (selected_feature_names, importance_dict, val_score)
    """
    from sklearn.ensemble import RandomForestRegressor
    
    # Fit Random Forest model
    rf = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    # Extract feature importances
    importance_dict = dict(zip(X_train.columns, rf.feature_importances_))
    
    # Select features above threshold
    selected_features = [feat for feat, imp in importance_dict.items() if imp >= threshold]
    
    # Calculate validation score
    val_score = rf.score(X_val, y_val)
    
    logger.info(f"RF selected {len(selected_features)} features with threshold={threshold}")
    
    return selected_features, importance_dict, val_score

def run_sensitivity_sweep(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    X_val: pd.DataFrame, 
    y_val: pd.Series,
    thresholds: List[float] = [0.01, 0.05, 0.1],
    n_iterations: int = 3
) -> pd.DataFrame:
    """
    Run feature selection sensitivity sweep over multiple thresholds and iterations.
    
    Args:
        X_train: Training features
        y_train: Training target
        X_val: Validation features
        y_val: Validation target
        thresholds: List of thresholds to test
        n_iterations: Number of iterations per threshold
        
    Returns:
        DataFrame with feature_id, threshold, and frequency
    """
    results = []
    
    for threshold in thresholds:
        selection_counts = {}
        
        for i in range(n_iterations):
            # Run RF selection with current threshold
            selected_features, _, _ = run_rf_selection(
                X_train, y_train, X_val, y_val, 
                threshold=threshold
            )
            
            for feat in selected_features:
                selection_counts[feat] = selection_counts.get(feat, 0) + 1
        
        # Calculate frequency for this threshold
        for feat, count in selection_counts.items():
            freq = count / n_iterations
            results.append({
                "feature_id": feat,
                "threshold": threshold,
                "frequency": freq
            })
    
    df = pd.DataFrame(results)
    logger.info(f"Sensitivity sweep completed: {len(df)} feature-threshold combinations")
    return df

def calculate_effect_sizes(
    X_train: pd.DataFrame, 
    y_train: pd.Series, 
    selected_features: List[str],
    method: str = "lasso"
) -> Dict[str, float]:
    """
    Calculate effect-size coefficients for selected features.
    
    Args:
        X_train: Training features (must contain selected features)
        y_train: Training target
        selected_features: List of feature names to calculate effects for
        method: Method to use for effect size calculation ('lasso' or 'rf')
        
    Returns:
        Dictionary mapping feature names to effect-size coefficients
    """
    # Filter X_train to only selected features
    X_selected = X_train[selected_features]
    
    if method == "lasso":
        from sklearn.linear_model import LinearRegression
        # Use LinearRegression to get coefficients (effect sizes)
        model = LinearRegression()
        model.fit(X_selected, y_train)
        coef_dict = dict(zip(selected_features, model.coef_))
        logger.info(f"Calculated effect sizes using Linear Regression for {len(selected_features)} features")
        
    elif method == "rf":
        from sklearn.ensemble import RandomForestRegressor
        # Use RF to get feature importances as effect proxies
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_selected, y_train)
        coef_dict = dict(zip(selected_features, model.feature_importances_))
        logger.info(f"Calculated effect sizes using Random Forest for {len(selected_features)} features")
        
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return coef_dict

def save_selection_frequency(df: pd.DataFrame, output_path: Optional[Path] = None):
    """
    Save selection frequency results to CSV.
    
    Args:
        df: DataFrame with feature_id, threshold, frequency
        output_path: Path to save the CSV file
    """
    if output_path is None:
        output_path = get_path("artifacts", "reports", "selection_frequency.csv")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved selection frequency to {output_path}")

def feature_selection_pipeline(
    split_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    thresholds: List[float] = [0.01, 0.05, 0.1],
    n_iterations: int = 3,
    lasso_alpha: float = 0.01
) -> Dict[str, Any]:
    """
    Run the complete feature selection pipeline.
    
    Args:
        split_dir: Directory containing split data
        output_dir: Directory to save results
        thresholds: Thresholds for sensitivity sweep
        n_iterations: Iterations per threshold
        lasso_alpha: Alpha for LASSO
        
    Returns:
        Dictionary containing pipeline results
    """
    if output_dir is None:
        output_dir = get_path("artifacts", "reports")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    X_train, y_train, X_val, y_val = load_split_data(split_dir)
    
    # Run sensitivity sweep
    logger.info("Running sensitivity sweep...")
    freq_df = run_sensitivity_sweep(X_train, y_train, X_val, y_val, thresholds, n_iterations)
    save_selection_frequency(freq_df, output_dir / "selection_frequency.csv")
    
    # Get top features (frequency > 0.5 across all thresholds)
    top_features = freq_df[freq_df['frequency'] > 0.5]['feature_id'].unique().tolist()
    
    if not top_features:
        logger.warning("No top features found with frequency > 0.5")
        # Fallback to all features if none selected
        top_features = X_train.columns.tolist()
    
    logger.info(f"Selected {len(top_features)} top features for effect size calculation")
    
    # Calculate effect sizes using LASSO
    logger.info("Calculating effect sizes...")
    effect_sizes = calculate_effect_sizes(X_train, y_train, top_features, method="lasso")
    
    # Save effect sizes
    effect_df = pd.DataFrame([
        {"feature_id": feat, "effect_size": coef}
        for feat, coef in effect_sizes.items()
    ])
    effect_df.to_csv(output_dir / "effect_sizes.csv", index=False)
    logger.info(f"Saved effect sizes for {len(effect_sizes)} features")
    
    return {
        "selected_features": top_features,
        "effect_sizes": effect_sizes,
        "selection_frequency": freq_df,
        "effect_sizes_path": str(output_dir / "effect_sizes.csv"),
        "selection_frequency_path": str(output_dir / "selection_frequency.csv")
    }

def main():
    """Main entry point for feature selection pipeline."""
    config = load_config()
    logger.info("Starting feature selection pipeline...")
    
    try:
        results = feature_selection_pipeline()
        logger.info("Feature selection pipeline completed successfully.")
        logger.info(f"Selected features: {len(results['selected_features'])}")
        logger.info(f"Effect sizes calculated: {len(results['effect_sizes'])}")
    except Exception as e:
        logger.error(f"Feature selection pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()