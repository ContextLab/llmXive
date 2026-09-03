"""
Iterative VIF-based feature exclusion and model retraining loop.

Implements the logic for T039: While any VIF > 10, exclude the feature with
the highest VIF, retrain the model using exact split indices and seed,
and recalculate VIF until all VIF <= 10.
"""
import logging
import os
import json
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score
from sklearn.model_selection import cross_val_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from code.config import SEED
from code.scaffold_split import get_murcko_scaffold, split_indices
from code.model_training import apply_log_transformation

logger = logging.getLogger(__name__)


def load_processed_data(path: str) -> pd.DataFrame:
    """Load the processed descriptor data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)


def prepare_features_and_target(
    df: pd.DataFrame,
    target_col: str,
    exclude_cols: List[str] = None
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix X and target vector y.
    Returns X, y, and list of feature names used.
    """
    exclude = exclude_cols or []
    feature_cols = [c for c in df.columns if c not in exclude and c != target_col]
    # Ensure we have numeric features
    X = df[feature_cols].select_dtypes(include=[np.number])
    y = df[target_col]
    if X.empty:
        raise ValueError("No numeric features remaining after exclusions.")
    return X.values, y.values, list(X.columns)


def train_model(X: np.ndarray, y: np.ndarray, model_type: str = "rf") -> Any:
    """Train a model (RF or GB) with fixed seed."""
    if model_type == "rf":
        return RandomForestRegressor(
            n_estimators=100,
            max_depth=None,
            random_state=SEED
        )
    elif model_type == "gb":
        return GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            random_state=SEED
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, float]:
    """Evaluate model with cross-validation and return metrics."""
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    return {
        "r2_mean": float(np.mean(scores)),
        "r2_std": float(np.std(scores)),
        "r2_scores": scores.tolist()
    }


def calculate_vif_scores(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for each feature.
    Returns dict mapping feature name -> VIF score.
    """
    if X.shape[1] == 0:
        return {}
    vif_data = {}
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[name] = float(vif)
        except Exception as e:
            logger.warning(f"Could not compute VIF for {name}: {e}")
            vif_data[name] = float('inf')
    return vif_data


def iterative_vif_retrain(
    df: pd.DataFrame,
    target_col: str,
    output_path: str,
    vif_threshold: float = 10.0,
    model_type: str = "rf",
    cv_folds: int = 5
) -> Dict[str, Any]:
    """
    Iteratively exclude features with VIF > threshold and retrain.

    Loop:
      1. Compute VIF for all current features.
      2. If max(VIF) <= threshold, stop.
      3. Else, exclude feature with HIGHEST VIF.
      4. Retrain model on reduced feature set.
      5. Repeat.

    Returns final results dict including excluded features, final VIFs, and model metrics.
    """
    # Exclude non-feature columns
    exclude_cols = ['smiles', 'status', target_col]
    excluded_features = []
    current_df = df.copy()

    logger.info(f"Starting iterative VIF exclusion loop (threshold={vif_threshold})")
    iteration = 0

    while True:
        iteration += 1
        logger.info(f"Iteration {iteration}: Current features = {len(current_df.columns) - len(exclude_cols) - 1}")

        # Prepare X, y
        try:
            X, y, feature_names = prepare_features_and_target(current_df, target_col, exclude_cols)
        except ValueError as e:
            logger.error(f"Feature preparation failed: {e}")
            break

        if len(feature_names) == 0:
            logger.warning("No features left to evaluate. Stopping loop.")
            break

        # Calculate VIF
        vif_scores = calculate_vif_scores(X, feature_names)
        max_vif_feature = max(vif_scores, key=vif_scores.get)
        max_vif = vif_scores[max_vif_feature]

        logger.info(f"  Max VIF: {max_vif:.2f} for feature '{max_vif_feature}'")

        # Check stopping condition
        if max_vif <= vif_threshold:
            logger.info(f"All VIFs <= {vif_threshold}. Stopping loop.")
            break

        # Exclude feature with highest VIF
        excluded_features.append(max_vif_feature)
        logger.warning(f"Excluding feature '{max_vif_feature}' (VIF={max_vif:.2f})")

        # Update exclude list
        exclude_cols.append(max_vif_feature)

        # Retrain model on reduced set
        X_reduced, y_reduced, _ = prepare_features_and_target(current_df, target_col, exclude_cols)
        model = train_model(X_reduced, y_reduced, model_type=model_type)
        metrics = evaluate_model(model, X_reduced, y_reduced, cv=cv_folds)

        logger.info(f"  Retrained {model_type} on {len(feature_names)-1} features. R2_mean={metrics['r2_mean']:.4f}")

        # Save intermediate results? (Optional, but we save final at end)

    # Final evaluation
    X_final, y_final, final_features = prepare_features_and_target(current_df, target_col, exclude_cols)
    final_model = train_model(X_final, y_final, model_type=model_type)
    final_metrics = evaluate_model(final_model, X_final, y_final, cv=cv_folds)
    final_vif = calculate_vif_scores(X_final, final_features)

    results = {
        "excluded_features": excluded_features,
        "final_features": final_features,
        "final_vif_scores": final_vif,
        "model_type": model_type,
        "model_metrics": final_metrics,
        "iterations": iteration,
        "threshold_used": vif_threshold
    }

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved iterative VIF retrain results to {output_path}")
    return results


def main():
    """CLI entry point for iterative VIF retraining."""
    import argparse

    parser = argparse.ArgumentParser(description="Iterative VIF-based feature exclusion and retraining")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON results")
    parser.add_argument("--target", type=str, default="log_conductivity", help="Target column name")
    parser.add_argument("--model", type=str, default="rf", choices=["rf", "gb"], help="Model type")
    parser.add_argument("--threshold", type=float, default=10.0, help="VIF threshold")
    parser.add_argument("--cv", type=int, default=5, help="Number of CV folds")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    df = load_processed_data(args.data)

    # Check if target column exists
    if args.target not in df.columns:
        # Try to find a log-transformed version
        possible_targets = [c for c in df.columns if c.startswith("log_")]
        if possible_targets:
            logger.warning(f"Target '{args.target}' not found. Using '{possible_targets[0]}'")
            args.target = possible_targets[0]
        else:
            raise ValueError(f"Target column '{args.target}' not found and no log_ columns available.")

    results = iterative_vif_retrain(
        df=df,
        target_col=args.target,
        output_path=args.output,
        vif_threshold=args.threshold,
        model_type=args.model,
        cv_folds=args.cv
    )

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
