"""
Feature Importance Analysis Module (T040).

Computes permutation importance on the final VIF-filtered model and saves
the ranked list to data/processed/feature_importance.csv.

Dependencies:
  - T039c: Final VIF-filtered model must exist (loaded via model_training.py or analysis.py).
  - T004: SEED constant.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from code.config import SEED, DATA_PATH
from code.logging_config import setup_logging

# Setup logging
logger = setup_logging(__name__)


def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the final processed data (descriptors.csv) and the target variable.
    Assumes T019b has written data/processed/descriptors.csv.
    Returns X (features) and y (target).
    """
    descriptors_path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    if not os.path.exists(descriptors_path):
        raise FileNotFoundError(f"Processed descriptors file not found: {descriptors_path}")

    df = pd.read_csv(descriptors_path)

    # Determine target column based on T026 logic (conductivity, HOMO_LUMO_gap, or proxy)
    # We check for common target names. T026 should have set the target column name.
    # For now, assume the column is named 'conductivity' or 'HOMO_LUMO_gap' or 'log_conductivity_proxy'.
    target_col = None
    candidates = ['conductivity', 'HOMO_LUMO_gap', 'log_conductivity_proxy']
    for cand in candidates:
        if cand in df.columns:
            target_col = cand
            break

    if target_col is None:
        # Fallback: check if any column looks like a target (e.g., ends with '_target')
        for col in df.columns:
            if 'target' in col.lower():
                target_col = col
                break

    if target_col is None:
        raise ValueError("Could not identify target variable in descriptors.csv. Expected one of: 'conductivity', 'HOMO_LUMO_gap', 'log_conductivity_proxy'")

    y = df[target_col]
    X = df.drop(columns=[target_col])

    return X, y


def prepare_features_and_target(X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepares feature matrix and target array for model training.
    Returns X_np, y_np, feature_names.
    """
    feature_names = list(X.columns)
    X_np = X.values
    y_np = y.values
    return X_np, y_np, feature_names


def train_model(X: np.ndarray, y: np.ndarray, model_type: str = 'rf') -> Any:
    """
    Trains a model on the provided data.
    model_type: 'rf' for Random Forest, 'gb' for Gradient Boosting.
    Uses the final VIF-filtered data (assumed to be passed in).
    """
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=SEED)
    elif model_type == 'gb':
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=SEED)
    else:
        raise ValueError(f"Unsupported model_type: {model_type}")

    model.fit(X, y)
    return model


def compute_feature_importance(model: Any, X: np.ndarray, y: np.ndarray, feature_names: List[str], n_repeats: int = 10) -> pd.DataFrame:
    """
    Computes permutation importance for the given model.
    Returns a DataFrame with 'feature' and 'importance_score'.
    """
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=SEED)

    importance_scores = result.importances_mean
    importance_std = result.importances_std

    df_importance = pd.DataFrame({
        'feature': feature_names,
        'importance_score': importance_scores,
        'importance_std': importance_std
    })

    # Sort by importance_score descending
    df_importance = df_importance.sort_values(by='importance_score', ascending=False).reset_index(drop=True)

    return df_importance


def save_feature_importance_csv(df_importance: pd.DataFrame, output_path: str) -> None:
    """
    Saves the feature importance DataFrame to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_importance.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")


def run_feature_importance_analysis(model_type: str = 'rf', n_repeats: int = 10) -> pd.DataFrame:
    """
    Main function to run the feature importance analysis.
    1. Load processed data.
    2. Train model (using final VIF-filtered data).
    3. Compute permutation importance.
    4. Save results to data/processed/feature_importance.csv.
    """
    logger.info("Starting feature importance analysis (T040)...")

    # Load data
    X, y = load_processed_data()
    X_np, y_np, feature_names = prepare_features_and_target(X, y)

    # Train model
    logger.info(f"Training {model_type} model on VIF-filtered data...")
    model = train_model(X_np, y_np, model_type)

    # Compute importance
    logger.info("Computing permutation importance...")
    df_importance = compute_feature_importance(model, X_np, y_np, feature_names, n_repeats)

    # Save results
    output_path = os.path.join(DATA_PATH, 'processed', 'feature_importance.csv')
    save_feature_importance_csv(df_importance, output_path)

    # Verify
    if os.path.exists(output_path):
        df_check = pd.read_csv(output_path)
        assert 'feature' in df_check.columns and 'importance_score' in df_check.columns
        logger.info("Feature importance analysis completed and verified.")
    else:
        raise RuntimeError("Failed to save feature importance CSV.")

    return df_importance


def main():
    """
    CLI entry point for T040.
    """
    parser = argparse.ArgumentParser(description="Compute feature importance rankings (T040).")
    parser.add_argument('--model', type=str, default='rf', choices=['rf', 'gb'], help="Model type: 'rf' (Random Forest) or 'gb' (Gradient Boosting).")
    parser.add_argument('--n_repeats', type=int, default=10, help="Number of repeats for permutation importance.")
    args = parser.parse_args()

    run_feature_importance_analysis(model_type=args.model, n_repeats=args.n_repeats)


if __name__ == "__main__":
    main()