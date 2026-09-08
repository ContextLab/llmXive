import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score

import config
from logging_config import setup_logging
from data_loader import load_processed_data
from scaffold_split import scaffold_split
from outlier_sensitivity import apply_threshold_filter, retrain_with_filtered_data

# Setup logging
logger = setup_logging(__name__)

def apply_log_transformation(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Apply natural log transformation to the target variable.
    Creates a new column 'log_{target_col}'.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    # Ensure values are positive for log transform
    if (df[target_col] <= 0).any():
        logger.warning("Non-positive values found in target variable. Adding small epsilon.")
        df[target_col] = df[target_col].replace(0, 1e-9)
        df[target_col] = df[target_col].clip(lower=1e-9)

    log_col = f"log_{target_col}"
    df[log_col] = np.log(df[target_col])
    logger.info(f"Applied log transformation to '{target_col}', created column '{log_col}'")
    return df

def train_models(
    X: np.ndarray, 
    y: np.ndarray, 
    seed: int = config.SEED
) -> Tuple[RandomForestRegressor, GradientBoostingRegressor]:
    """
    Train Random Forest and Gradient Boosting models.
    """
    logger.info("Training Random Forest model...")
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=seed
    )
    rf.fit(X, y)

    logger.info("Training Gradient Boosting model...")
    gb = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        random_state=seed
    )
    gb.fit(X, y)

    return rf, gb

def run_cross_validation(
    X: np.ndarray, 
    y: np.ndarray, 
    model: Any, 
    cv: int = 5,
    scoring: str = 'r2'
) -> Dict[str, float]:
    """
    Run cross-validation and return mean/std scores.
    """
    scores = cross_val_score(model, X, y, cv=cv, scoring=scoring)
    return {
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "scores": scores.tolist()
    }

def save_model_results(
    rf_r2: float, 
    gb_r2: float, 
    cv_scores: Dict[str, Any], 
    output_path: str,
    sensitivity_analysis: Optional[Dict[str, Any]] = None,
    vif_scores: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save model results to a JSON file.
    """
    results = {
        "rf_r2": rf_r2,
        "gb_r2": gb_r2,
        "cv_scores": cv_scores,
        "sensitivity_analysis": sensitivity_analysis if sensitivity_analysis else {},
        "vif_scores": vif_scores if vif_scores else {}
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train models on processed data.")
    parser.add_argument('--data', type=str, required=True, help='Path to processed data CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output results JSON')
    parser.add_argument('--target', type=str, default=config.TARGET_VAR, help='Target variable name')
    parser.add_argument('--sigma', type=float, default=config.OUTLIER_SIGMA, help='Outlier threshold sigma')
    args = parser.parse_args()

    logger.info(f"Loading data from {args.data}")
    df = load_processed_data(args.data)

    # Validate target
    if args.target not in df.columns:
        # Check for log version if original not found
        log_target = f"log_{args.target}"
        if log_target in df.columns:
            target_col = log_target
            logger.info(f"Using existing log-transformed target: {log_target}")
        else:
            # Try to find conductivity or HOMO-LUMO
            potential_targets = ['conductivity', 'charge_carrier_mobility', 'HOMO_LUMO_gap']
            found_target = None
            for t in potential_targets:
                if t in df.columns:
                    found_target = t
                    break
            
            if not found_target:
                logger.error("No valid target variable found.")
                sys.exit(1)
            
            logger.warning(f"Target '{args.target}' not found. Using '{found_target}' instead.")
            target_col = found_target
    else:
        target_col = args.target

    # Apply log transformation if not already done
    if not target_col.startswith('log_'):
        df = apply_log_transformation(df, target_col)
        target_col = f"log_{target_col}"

    # Filter outliers
    logger.info(f"Filtering outliers with sigma={args.sigma}")
    # Assuming filter_outliers is in analysis or outlier_sensitivity
    from analysis import filter_outliers
    df_filtered = filter_outliers(df, target_col, args.sigma)

    # Prepare features and target
    feature_cols = [c for c in df_filtered.columns if c != target_col]
    X = df_filtered[feature_cols].values
    y = df_filtered[target_col].values

    # Split data
    train_indices, test_indices = scaffold_split(df_filtered, seed=config.SEED)
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]

    # Train models
    rf, gb = train_models(X_train, y_train)

    # Evaluate on test set
    rf_pred = rf.predict(X_test)
    gb_pred = gb.predict(X_test)

    rf_r2 = r2_score(y_test, rf_pred)
    gb_r2 = r2_score(y_test, gb_pred)

    # Cross-validation
    logger.info("Running cross-validation...")
    cv_scores_rf = run_cross_validation(X_train, y_train, rf)
    cv_scores_gb = run_cross_validation(X_train, y_train, gb)

    # Run sensitivity analysis (T032 logic)
    sensitivity_results = {}
    try:
        from analysis import run_sensitivity_analysis
        sensitivity_results = run_sensitivity_analysis(
            df_filtered, 
            target_col, 
            thresholds=[2.5, 3.0, 3.5],
            seed=config.SEED
        )
    except Exception as e:
        logger.warning(f"Sensitivity analysis failed: {e}. Saving empty results.")
        sensitivity_results = {"thresholds": [], "r2_scores": [], "r2_variance": 0.0}

    # Save results
    save_model_results(
        rf_r2=rf_r2,
        gb_r2=gb_r2,
        cv_scores={"rf": cv_scores_rf, "gb": cv_scores_gb},
        output_path=args.output,
        sensitivity_analysis=sensitivity_results
    )

if __name__ == "__main__":
    main()
