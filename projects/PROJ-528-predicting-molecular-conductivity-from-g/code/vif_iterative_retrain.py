"""
Task T039: Implement iterative retraining loop for VIF filtering.

This module implements the iterative process where features with VIF > 10
are excluded one by one (highest VIF first), and the model is retrained
after each exclusion until all remaining features have VIF <= 10.

It uses the exact split indices from T027 (scaffold_split) and the random
seed from T004 (config).
"""
import logging
import os
import json
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from code.config import SEED, VIF_THRESHOLD
from code.vif_analysis import calculate_vif, get_high_vif_features
from code.scaffold_split import scaffold_split
from code.logging_config import setup_logging

# Ensure logging is configured
setup_logging()
logger = logging.getLogger(__name__)

def load_processed_data(data_path: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """Load the processed descriptor data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    df = pd.read_csv(data_path)
    # Ensure status is 'valid'
    if 'status' in df.columns:
        df = df[df['status'] == 'valid'].copy()
    return df

def prepare_features_and_target(
    df: pd.DataFrame,
    target_col: str,
    exclude_cols: Optional[List[str]] = None
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare features (X) and target (y) from the dataframe.
    Excludes non-feature columns and specified exclude_cols.
    Returns X, y, and the list of feature names used.
    """
    exclude_default = ['smiles', 'status', 'conductivity', 'HOMO_LUMO_gap', 'target']
    if exclude_cols:
        exclude_default.extend(exclude_cols)

    feature_cols = [col for col in df.columns if col not in exclude_default]

    # Ensure we have numeric features
    X = df[feature_cols].select_dtypes(include=[np.number]).values
    y = df[target_col].values

    return X, y, feature_cols

def train_model(X_train: np.ndarray, y_train: np.ndarray, model_type: str = 'rf') -> Any:
    """Train a model (RF or GB) on the given data."""
    if model_type == 'rf':
        model = RandomForestRegressor(
            n_estimators=100,
            random_state=SEED,
            n_jobs=-1
        )
    elif model_type == 'gb':
        model = GradientBoostingRegressor(
            n_estimators=100,
            random_state=SEED
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate the model and return metrics."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    return {'r2': r2, 'mae': mae}

def iterative_vif_retrain(
    data_path: str = "data/processed/descriptors.csv",
    target_col: str = "conductivity",
    model_type: str = "rf",
    output_path: str = "data/processed/vif_retraining_log.json",
    vif_threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Iteratively remove features with VIF > threshold and retrain the model.

    Process:
    1. Load data and prepare X, y.
    2. While any feature has VIF > threshold:
       a. Calculate VIF for all current features.
       b. Identify the feature with the highest VIF.
       c. Remove that feature from X.
       d. Retrain the model on the reduced feature set.
       e. Record the state (removed feature, remaining features, metrics).
    3. Save the full log to output_path.

    Returns the final log dictionary.
    """
    logger.info(f"Starting iterative VIF retraining with threshold={vif_threshold}")

    # Load data
    df = load_processed_data(data_path)
    if target_col not in df.columns:
        # Fallback to HOMO_LUMO_gap if conductivity missing
        if 'HOMO_LUMO_gap' in df.columns:
            logger.warning(f"Target '{target_col}' not found. Using 'HOMO_LUMO_gap'.")
            target_col = 'HOMO_LUMO_gap'
        else:
            raise ValueError("Neither 'conductivity' nor 'HOMO_LUMO_gap' found in data.")

    # Perform scaffold split to get train/test indices
    # We need to pass the dataframe with a 'smiles' column for scaffold split
    # Assuming 'smiles' is present
    if 'smiles' not in df.columns:
        raise ValueError("Dataframe must contain 'smiles' column for scaffold split.")

    # We'll use a fixed seed from config
    train_idx, test_idx = scaffold_split(
        df,
        smiles_col='smiles',
        test_size=0.2,
        random_state=SEED
    )

    X_full, y_full, all_feature_cols = prepare_features_and_target(df, target_col)

    # Initial feature set
    current_feature_indices = list(range(len(all_feature_cols)))
    current_feature_names = [all_feature_cols[i] for i in current_feature_indices]

    log_entries = []
    iteration = 0

    while True:
        iteration += 1
        logger.info(f"Iteration {iteration}: Evaluating VIF for {len(current_feature_names)} features")

        # Get current X
        X_current = X_full[:, current_feature_indices]

        # Calculate VIF for current features
        vif_scores = calculate_vif(X_current)

        # Check if any VIF > threshold
        high_vif_mask = np.array(vif_scores) > vif_threshold
        if not np.any(high_vif_mask):
            logger.info(f"Iteration {iteration}: All features have VIF <= {vif_threshold}. Stopping.")
            break

        # Find the feature with the highest VIF
        max_vif_idx_in_current = int(np.argmax(vif_scores))
        max_vif_feature_name = current_feature_names[max_vif_idx_in_current]
        max_vif_value = vif_scores[max_vif_idx_in_current]

        logger.warning(f"Iteration {iteration}: Removing feature '{max_vif_feature_name}' (VIF={max_vif_value:.2f})")

        # Remove the feature from our index list
        # current_feature_indices is a list of indices into the original X_full
        # We need to remove the element at position max_vif_idx_in_current from current_feature_indices
        idx_to_remove = current_feature_indices[max_vif_idx_in_current]
        current_feature_indices.pop(max_vif_idx_in_current)
        current_feature_names.pop(max_vif_idx_in_current)

        # Retrain model on the reduced feature set
        X_train = X_full[train_idx][:, current_feature_indices]
        y_train = y_full[train_idx]
        X_test = X_full[test_idx][:, current_feature_indices]
        y_test = y_full[test_idx]

        model = train_model(X_train, y_train, model_type)
        metrics = evaluate_model(model, X_test, y_test)

        log_entry = {
            "iteration": iteration,
            "removed_feature": max_vif_feature_name,
            "removed_vif": float(max_vif_value),
            "remaining_features": current_feature_names,
            "remaining_count": len(current_feature_names),
            "metrics": metrics
        }
        log_entries.append(log_entry)

        # Safety break to prevent infinite loops (though VIF should eventually drop)
        if len(current_feature_names) <= 1:
            logger.warning("Only one feature remaining. Stopping to avoid empty feature set.")
            break

    # Final model evaluation
    if current_feature_names:
        X_train = X_full[train_idx][:, current_feature_indices]
        y_train = y_full[train_idx]
        X_test = X_full[test_idx][:, current_feature_indices]
        y_test = y_full[test_idx]
        final_model = train_model(X_train, y_train, model_type)
        final_metrics = evaluate_model(final_model, X_test, y_test)
        final_vif = calculate_vif(X_test)
    else:
        final_metrics = {'r2': 0.0, 'mae': 0.0}
        final_vif = []

    result = {
        "threshold": vif_threshold,
        "model_type": model_type,
        "total_iterations": len(log_entries),
        "removed_features": [entry["removed_feature"] for entry in log_entries],
        "log": log_entries,
        "final_features": current_feature_names,
        "final_metrics": final_metrics,
        "final_vif_scores": final_vif
    }

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"VIF retraining log saved to {output_path}")
    return result

def main():
    """Entry point for the script."""
    logger.info("Running iterative VIF retraining (T039)")
    try:
        result = iterative_vif_retrain(
            data_path="data/processed/descriptors.csv",
            target_col="conductivity",
            model_type="rf",
            output_path="data/processed/vif_retraining_log.json",
            vif_threshold=VIF_THRESHOLD
        )
        logger.info(f"Completed. Final R2: {result['final_metrics']['r2']:.4f}")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error during iterative VIF retraining: {e}")
        raise

if __name__ == "__main__":
    main()
