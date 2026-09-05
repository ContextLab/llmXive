import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from code.logging_config import setup_logging
from code.data_loader import load_processed_data
from code.scaffold_split import scaffold_split
from code.config import SEED

def train_models(
    X_train: np.ndarray, 
    y_train: np.ndarray, 
    X_test: np.ndarray, 
    y_test: np.ndarray, 
    seed: int = SEED
) -> Tuple[RandomForestRegressor, GradientBoostingRegressor]:
    """
    Train Random Forest and Gradient Boosting models.
    """
    rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=seed)
    
    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)
    
    return rf, gb

def main():
    parser = argparse.ArgumentParser(description="Train models on processed data.")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data CSV.")
    parser.add_argument("--output", type=str, required=True, help="Path to output results JSON.")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info(f"Loading data from {args.data}")
    try:
        df = load_processed_data(args.data)
    except Exception as e:
        logger.error(f"Failed to load data via helper: {e}")
        df = pd.read_csv(args.data)
    
    if df.empty:
        logger.error("Dataframe is empty.")
        return

    # Identify target
    target_col = 'log_conductivity' if 'log_conductivity' in df.columns else 'log_HOMO_LUMO_gap'
    if target_col not in df.columns:
        # Fallback
        candidates = [c for c in df.columns if 'target' in c.lower() or 'conductivity' in c.lower()]
        if candidates:
            target_col = candidates[0]
        else:
            logger.error("No target variable found.")
            return

    feature_cols = [c for c in df.columns if c not in ['smiles', target_col, 'status', 'error_msg'] and df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        logger.error("No feature columns found.")
        return

    X = df[feature_cols].values
    y = df[target_col].values

    # Handle NaNs
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    df = df[mask]

    if len(X) < 20:
        logger.error("Not enough samples after cleaning.")
        return

    # Split
    if 'smiles' in df.columns:
        try:
            train_idx, test_idx = scaffold_split(df, 'smiles', test_size=0.2, seed=SEED)
        except Exception as e:
            logger.warning(f"Scaffold split failed: {e}. Using random split.")
            indices = np.arange(len(df))
            np.random.seed(SEED)
            np.random.shuffle(indices)
            split_point = int(0.8 * len(indices))
            train_idx = indices[:split_point]
            test_idx = indices[split_point:]
    else:
        indices = np.arange(len(df))
        np.random.seed(SEED)
        np.random.shuffle(indices)
        split_point = int(0.8 * len(indices))
        train_idx = indices[:split_point]
        test_idx = indices[split_point:]

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    logger.info(f"Training models on {len(X_train)} samples. Testing on {len(X_test)}.")
    rf_model, gb_model = train_models(X_train, y_train, X_test, y_test, seed=SEED)

    r2_rf = rf_model.score(X_test, y_test)
    r2_gb = gb_model.score(X_test, y_test)

    # Cross validation
    cv_scores_rf = cross_val_score(rf_model, X_train, y_train, cv=5, scoring='r2')
    cv_scores_gb = cross_val_score(gb_model, X_train, y_train, cv=5, scoring='r2')

    results = {
        "rf_r2": float(r2_rf),
        "gb_r2": float(r2_gb),
        "cv_scores_rf": cv_scores_rf.tolist(),
        "cv_scores_gb": cv_scores_gb.tolist(),
        "metrics": {
            "rf_mean_r2": float(np.mean(cv_scores_rf)),
            "rf_std_r2": float(np.std(cv_scores_rf)),
            "gb_mean_r2": float(np.mean(cv_scores_gb)),
            "gb_std_r2": float(np.std(cv_scores_gb))
        }
    }

    # Save
    ensure_output_dir = lambda p: os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
    ensure_output_dir(args.output)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {args.output}")

if __name__ == "__main__":
    main()
