"""
Feature Importance Analysis Module.

Computes feature importance rankings using permutation importance on the
final VIF-filtered model and saves the results to a CSV file.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional

from sklearn.inspection import permutation_importance
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from code.config import SEED, DATA_PATH
from code.logging_config import setup_logging

# Setup logging
logger = setup_logging(__name__)


def load_processed_data(filepath: str) -> pd.DataFrame:
    """
    Load the processed descriptor data.

    Args:
        filepath: Path to the CSV file containing descriptors.

    Returns:
        DataFrame with molecular descriptors.
    """
    if not os.path.exists(filepath):
        logger.error(f"Processed data file not found: {filepath}")
        raise FileNotFoundError(f"Processed data file not found: {filepath}")

    df = pd.read_csv(filepath)

    # Identify target column (log_conductivity or log_HOMO_LUMO_gap)
    target_cols = [c for c in df.columns if c.startswith('log_')]
    if not target_cols:
        logger.error("No log-transformed target variable found in data.")
        raise ValueError("No log-transformed target variable found.")

    # Assume the first log_ column is the target if multiple exist, or specific one
    target_col = target_cols[0]
    logger.info(f"Using target variable: {target_col}")

    return df, target_col


def prepare_features_and_target(df: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix and target vector, excluding non-feature columns.

    Args:
        df: DataFrame containing features and target.
        target_col: Name of the target column.

    Returns:
        Tuple of (X, y, feature_names)
    """
    # Columns to exclude: 'smiles', 'status', and the target column
    exclude_cols = ['smiles', 'status', target_col]
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    X = df[feature_cols].values
    y = df[target_col].values
    feature_names = feature_cols

    # Handle any remaining NaNs or Infs in features
    if np.any(~np.isfinite(X)):
        logger.warning("Non-finite values found in feature matrix. Replacing with 0.")
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    if np.any(~np.isfinite(y)):
        logger.warning("Non-finite values found in target vector. Dropping rows.")
        valid_mask = np.isfinite(y)
        X = X[valid_mask]
        y = y[valid_mask]

    return X, y, feature_names


def train_model(X: np.ndarray, y: np.ndarray, model_type: str = 'rf') -> Any:
    """
    Train a regression model.

    Args:
        X: Feature matrix.
        y: Target vector.
        model_type: 'rf' for Random Forest, 'gb' for Gradient Boosting.

    Returns:
        Trained model instance.
    """
    if model_type == 'rf':
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=None,
            random_state=SEED,
            n_jobs=-1
        )
    elif model_type == 'gb':
        model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            random_state=SEED,
            max_depth=5
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    model.fit(X, y)
    return model


def compute_feature_importance(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_repeats: int = 10
) -> pd.DataFrame:
    """
    Compute permutation importance for a trained model.

    Args:
        model: Trained scikit-learn model.
        X: Feature matrix.
        y: Target vector.
        feature_names: List of feature names.
        n_repeats: Number of permutation repeats.

    Returns:
        DataFrame with feature names and importance scores, ranked by importance.
    """
    logger.info(f"Computing permutation importance with {n_repeats} repeats...")

    result = permutation_importance(
        model, X, y,
        n_repeats=n_repeats,
        random_state=SEED,
        n_jobs=-1
    )

    # Extract mean importance scores
    importance_scores = result.importances_mean

    # Create DataFrame
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance_score': importance_scores
    })

    # Sort by importance score descending
    importance_df = importance_df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)

    logger.info(f"Computed importance for {len(importance_df)} features.")
    return importance_df


def save_feature_importance_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the feature importance ranking to a CSV file.

    Args:
        df: DataFrame with feature and importance_score columns.
        output_path: Path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")


def run_feature_importance_analysis(
    data_path: str,
    output_path: str,
    model_type: str = 'rf'
) -> pd.DataFrame:
    """
    Run the full feature importance analysis pipeline.

    1. Load data.
    2. Train model (assuming data is already VIF-filtered or using the final state).
    3. Compute permutation importance.
    4. Save to CSV.

    Args:
        data_path: Path to the processed descriptors CSV.
        output_path: Path to save the feature importance CSV.
        model_type: Type of model to train ('rf' or 'gb').

    Returns:
        DataFrame with feature importance rankings.
    """
    # Load data
    df, target_col = load_processed_data(data_path)

    # Prepare features
    X, y, feature_names = prepare_features_and_target(df, target_col)

    if len(X) == 0:
        logger.error("No valid data points remaining after preprocessing.")
        raise ValueError("No valid data points.")

    # Train model
    logger.info(f"Training {model_type} model for importance analysis...")
    model = train_model(X, y, model_type)

    # Evaluate briefly
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    logger.info(f"Model trained. R²: {r2:.4f}, MAE: {mae:.4f}")

    # Compute importance
    importance_df = compute_feature_importance(model, X, y, feature_names)

    # Save results
    save_feature_importance_csv(importance_df, output_path)

    return importance_df


def main():
    """
    CLI entry point for feature importance analysis.
    """
    parser = argparse.ArgumentParser(description="Compute and save feature importance rankings.")
    parser.add_argument(
        "--data",
        type=str,
        default="data/processed/descriptors.csv",
        help="Path to the processed descriptors CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/feature_importance.csv",
        help="Path to save the feature importance CSV file."
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=['rf', 'gb'],
        default='rf',
        help="Model type to use for importance calculation (rf or gb)."
    )

    args = parser.parse_args()

    # Ensure logging is configured
    setup_logging(__name__)

    try:
        run_feature_importance_analysis(args.data, args.output, args.model)
        logger.info("Feature importance analysis completed successfully.")
    except Exception as e:
        logger.error(f"Feature importance analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()