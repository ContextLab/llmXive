"""
Feature Importance Analysis Module.

Computes permutation importance for the final VIF-filtered model and saves
the ranked list to data/processed/feature_importance.csv.
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

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load the processed descriptors and target variable.
    Returns X (features), y (target), and the original dataframe for reference.
    """
    descriptors_path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    results_path = os.path.join(DATA_PATH, 'processed', 'model_results.json')

    if not os.path.exists(descriptors_path):
        raise FileNotFoundError(f"Descriptors file not found at {descriptors_path}. "
                                "Run T019b to generate descriptors first.")

    df = pd.read_csv(descriptors_path)

    # Determine target variable from model_results.json or config
    target_var = 'conductivity'
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            results = json.load(f)
            if 'target_variable' in results:
                target_var = results['target_variable']

    # Check if log-transformed target exists
    log_target_col = f"log_{target_var}"
    if log_target_col in df.columns:
        y = df[log_target_col]
    elif target_var in df.columns:
        logger.warning(f"Log-transformed target {log_target_col} not found. Using raw target {target_var}.")
        y = df[target_var]
    else:
        raise ValueError(f"Target variable '{target_var}' or its log version not found in descriptors.")

    # Features are all columns except the target and 'smiles'
    feature_cols = [col for col in df.columns if col not in [target_var, log_target_col, 'smiles']]
    X = df[feature_cols]

    return X, y, df

def prepare_features_and_target() -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Prepare features and target, ensuring no NaN values remain.
    Returns X, y, and the list of feature names.
    """
    X, y, df = load_processed_data()

    # Drop rows with any NaN in features or target
    combined = pd.concat([X, y], axis=1)
    combined = combined.dropna()
    X = combined[X.columns]
    y = combined[y.name]

    return X, y, X.columns.tolist()

def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """
    Train a Random Forest model on the provided data.
    Uses the same parameters as T029.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=SEED,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def compute_feature_importance(model: Any, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """
    Compute permutation importance.
    Returns a DataFrame with 'feature' and 'importance_score' columns.
    """
    result = permutation_importance(
        model, X, y,
        n_repeats=10,
        random_state=SEED,
        n_jobs=-1
    )

    importance_scores = result.importances_mean
    features = X.columns

    # Create DataFrame
    importance_df = pd.DataFrame({
        'feature': features,
        'importance_score': importance_scores
    })

    # Sort by importance score descending
    importance_df = importance_df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)

    return importance_df

def save_feature_importance_csv(importance_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the feature importance ranking to a CSV file.
    """
    importance_df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to {output_path}")

    # Verify file exists and has content
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Failed to create file at {output_path}")

    loaded_df = pd.read_csv(output_path)
    if 'feature' not in loaded_df.columns or 'importance_score' not in loaded_df.columns:
        raise ValueError(f"Output file {output_path} does not contain required columns.")

    logger.info(f"Verification passed: {len(loaded_df)} features ranked.")

def run_feature_importance_analysis() -> pd.DataFrame:
    """
    Main function to run the full feature importance analysis pipeline.
    """
    logger.info("Starting feature importance analysis (T040).")

    # Prepare data
    X, y, feature_names = prepare_features_and_target()
    logger.info(f"Loaded {len(X)} samples with {len(feature_names)} features.")

    # Train model
    model = train_model(X, y)
    logger.info("Model trained successfully.")

    # Compute importance
    importance_df = compute_feature_importance(model, X, y)
    logger.info("Permutation importance computed.")

    # Save output
    output_path = os.path.join(DATA_PATH, 'processed', 'feature_importance.csv')
    save_feature_importance_csv(importance_df, output_path)

    logger.info("Feature importance analysis completed successfully.")
    return importance_df

def main():
    """
    CLI entry point for T040.
    """
    try:
        run_feature_importance_analysis()
    except Exception as e:
        logger.error(f"Feature importance analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()