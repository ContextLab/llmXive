"""
Cognitive Load Estimation Model Training Pipeline.

This module implements feature engineering, model training, and validation
for predicting cognitive load scores from student interaction data.

Key Features:
- Log-transform latency features to handle skew
- Aggregate error/hint/pause counts per session
- Train Gradient Boosting Regressor (LightGBM)
- Validate against Golden Set with Pearson correlation
"""

import os
import sys
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr
import lightgbm as lgb

# Import project utilities
from utils import get_logger, calculate_vif, check_vif_threshold
from load_data import load_and_verify_datasets, validate_golden_set

# Configure logging
logger = get_logger(__name__)

# Constants
GOLDEN_SET_PATH = "data/processed/golden_set.csv"
MODEL_OUTPUT_PATH = "data/processed/load_model.pkl"
TARGET_COLUMN = "expert_load_score"
MIN_SAMPLE_SIZE = 40
TARGET_CORRELATION = 0.6
MAX_VIF_THRESHOLD = 5.0
RANDOM_SEED = 42


def log_transform_latency(df: pd.DataFrame, latency_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Apply log-transform to latency features to reduce skewness.

    Args:
        df: Input DataFrame with interaction data
        latency_columns: List of column names to transform. If None, auto-detect.

    Returns:
        DataFrame with log-transformed latency columns
    """
    df_transformed = df.copy()

    if latency_columns is None:
        # Auto-detect latency columns
        latency_columns = [col for col in df.columns if 'latency' in col.lower() or 'response_time' in col.lower()]

    for col in latency_columns:
        if col in df_transformed.columns:
            # Add small epsilon to avoid log(0)
            df_transformed[col] = np.log1p(df_transformed[col].replace(0, np.nan).fillna(0))
            logger.debug(f"Applied log-transform to column: {col}")

    return df_transformed


def aggregate_interaction_counts(df: pd.DataFrame, session_col: str = "session_id") -> pd.DataFrame:
    """
    Count errors, hints, and pauses per session.

    Args:
        df: Input DataFrame with interaction data
        session_col: Column name identifying unique sessions

    Returns:
        DataFrame with aggregated counts per session
    """
    if session_col not in df.columns:
        logger.warning(f"Session column '{session_col}' not found. Returning original DataFrame.")
        return df

    # Define feature columns to aggregate
    count_features = {
        'error': [col for col in df.columns if 'error' in col.lower()],
        'hint': [col for col in df.columns if 'hint' in col.lower()],
        'pause': [col for col in df.columns if 'pause' in col.lower()]
    }

    agg_dict = {}
    for feature_type, cols in count_features.items():
        for col in cols:
            if col in df.columns:
                agg_dict[col] = 'sum'
                logger.debug(f"Will aggregate column: {col} as sum")

    if not agg_dict:
        logger.warning("No count features found for aggregation.")
        return df

    # Group by session and aggregate
    session_agg = df.groupby(session_col).agg(agg_dict).reset_index()

    # Rename columns for clarity
    session_agg.columns = [session_col] + [f"{col}_count" for col in agg_dict.keys()]

    return session_agg


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main feature engineering pipeline.

    Steps:
    1. Log-transform latency features
    2. Aggregate interaction counts per session
    3. Merge aggregated counts back to original data (if session-based)
    4. Handle missing values

    Args:
        df: Raw interaction DataFrame

    Returns:
        Engineered feature DataFrame
    """
    logger.info("Starting feature engineering pipeline...")

    # Step 1: Log-transform latency
    df_engineered = log_transform_latency(df)

    # Step 2: Aggregate counts per session
    if "session_id" in df_engineered.columns:
        session_agg = aggregate_interaction_counts(df_engineered, session_col="session_id")

        # Merge aggregated counts back to original data
        df_engineered = df_engineered.merge(
            session_agg,
            on="session_id",
            how="left"
        )
        logger.info(f"Merged session aggregates. New columns: {session_agg.columns.tolist()}")
    else:
        logger.warning("No session_id found. Skipping session aggregation.")

    # Step 3: Handle missing values
    # Fill numeric NaNs with 0 (for counts) or median (for continuous features)
    numeric_cols = df_engineered.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_engineered[col].isna().any():
            # Check if it's a count column (sum of non-negative values)
            if col.endswith('_count'):
                df_engineered[col] = df_engineered[col].fillna(0)
            else:
                df_engineered[col] = df_engineered[col].fillna(df_engineered[col].median())
            logger.debug(f"Filled NaN in {col} with {'0' if col.endswith('_count') else 'median'}")

    # Drop non-numeric columns except session_id and target
    cols_to_keep = ['session_id', TARGET_COLUMN] + [
        col for col in df_engineered.columns
        if df_engineered[col].dtype in [np.int64, np.float64]
        and col not in ['session_id', TARGET_COLUMN]
    ]
    df_engineered = df_engineered[[col for col in cols_to_keep if col in df_engineered.columns]]

    logger.info(f"Feature engineering complete. Final shape: {df_engineered.shape}")
    logger.info(f"Feature columns: {df_engineered.columns.tolist()}")

    return df_engineered


def check_collinearity(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate VIF for features and flag high collinearity.

    Args:
        df: DataFrame with features
        feature_cols: List of feature column names

    Returns:
        Dictionary mapping feature names to VIF values
    """
    logger.info("Checking collinearity (VIF) for features...")
    vif_scores = calculate_vif(df[feature_cols])

    high_vif = {k: v for k, v in vif_scores.items() if v > MAX_VIF_THRESHOLD}
    if high_vif:
        logger.warning(f"High VIF detected (> {MAX_VIF_THRESHOLD}): {high_vif}")
    else:
        logger.info("All VIF scores within acceptable range.")

    return vif_scores


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = RANDOM_SEED
) -> Tuple[lgb.LGBMRegressor, Dict[str, Any]]:
    """
    Train a LightGBM Gradient Boosting Regressor.

    Args:
        X: Feature matrix
        y: Target vector
        test_size: Proportion of data for validation
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (trained model, metrics dict)
    """
    logger.info("Training LightGBM model...")

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Create LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    # Model parameters (CPU-only, hist algorithm)
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'tree_method': 'hist',
        'device': 'cpu',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'seed': random_state
    }

    # Train model
    model = lgb.train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
    )

    # Evaluate
    y_pred = model.predict(X_val)

    metrics = {
        'rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
        'r2': r2_score(y_val, y_pred),
        'pearson_r': pearsonr(y_val, y_pred)[0],
        'n_train': len(y_train),
        'n_val': len(y_val)
    }

    logger.info(f"Model training complete. Metrics: {metrics}")

    return model, metrics


def validate_against_golden_set(
    model: lgb.LGBMRegressor,
    feature_cols: List[str],
    golden_set_path: str = GOLDEN_SET_PATH
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate model predictions against the Golden Set.

    Args:
        model: Trained model
        feature_cols: List of feature column names used for training
        golden_set_path: Path to the Golden Set CSV

    Returns:
        Tuple of (success bool, validation metrics dict)
    """
    logger.info(f"Validating against Golden Set: {golden_set_path}")

    # Load Golden Set
    try:
        golden_df = pd.read_csv(golden_set_path)
    except FileNotFoundError:
        logger.error(f"Golden Set not found at {golden_set_path}")
        return False, {"error": "Golden Set file not found"}

    # Ensure required columns exist
    if TARGET_COLUMN not in golden_df.columns:
        logger.error(f"Target column '{TARGET_COLUMN}' not found in Golden Set")
        return False, {"error": f"Missing target column: {TARGET_COLUMN}"}

    # Filter to feature columns
    available_features = [col for col in feature_cols if col in golden_df.columns]
    if len(available_features) < len(feature_cols):
        missing = set(feature_cols) - set(available_features)
        logger.warning(f"Missing features in Golden Set: {missing}")
        # Only proceed if we have enough features
        if len(available_features) < 3:
            return False, {"error": "Insufficient features in Golden Set"}

    X_golden = golden_df[available_features]
    y_golden = golden_df[TARGET_COLUMN]

    # Predict
    y_pred = model.predict(X_golden)

    # Calculate correlation
    corr, p_value = pearsonr(y_golden, y_pred)

    validation_metrics = {
        'pearson_r': corr,
        'p_value': p_value,
        'n_samples': len(y_golden),
        'target_met': corr >= TARGET_CORRELATION
    }

    logger.info(f"Validation against Golden Set: r={corr:.3f}, p={p_value:.3e}")

    success = corr >= TARGET_CORRELATION and len(y_golden) >= MIN_SAMPLE_SIZE
    if not success:
        reason = []
        if corr < TARGET_CORRELATION:
            reason.append(f"Correlation {corr:.3f} < target {TARGET_CORRELATION}")
        if len(y_golden) < MIN_SAMPLE_SIZE:
            reason.append(f"Sample size {len(y_golden)} < min {MIN_SAMPLE_SIZE}")
        logger.warning(f"Validation failed: {'; '.join(reason)}")

    return success, validation_metrics


def main():
    """
    Main entry point for the training pipeline.
    """
    logger.info("=== Starting Cognitive Load Model Training ===")

    # 1. Load and verify datasets
    logger.info("Loading datasets...")
    raw_data = load_and_verify_datasets()
    if raw_data is None or raw_data.empty:
        logger.error("Failed to load valid datasets.")
        sys.exit(1)

    # 2. Validate Golden Set existence
    logger.info("Validating Golden Set...")
    if not validate_golden_set(GOLDEN_SET_PATH):
        logger.error("Golden Set validation failed. Cannot proceed.")
        sys.exit(1)

    # 3. Feature Engineering
    logger.info("Performing feature engineering...")
    df_engineered = engineer_features(raw_data)

    # 4. Prepare training data
    if TARGET_COLUMN not in df_engineered.columns:
        logger.error(f"Target column '{TARGET_COLUMN}' not found after engineering.")
        sys.exit(1)

    # Drop rows with missing target
    df_clean = df_engineered.dropna(subset=[TARGET_COLUMN])

    if len(df_clean) < MIN_SAMPLE_SIZE:
        logger.error(f"Insufficient samples ({len(df_clean)}) after cleaning. Need >= {MIN_SAMPLE_SIZE}")
        sys.exit(1)

    # Define features (exclude session_id and target)
    feature_cols = [col for col in df_clean.columns if col not in ['session_id', TARGET_COLUMN]]

    if not feature_cols:
        logger.error("No feature columns found after cleaning.")
        sys.exit(1)

    X = df_clean[feature_cols]
    y = df_clean[TARGET_COLUMN]

    # 5. Check collinearity
    vif_scores = check_collinearity(X, feature_cols)

    # 6. Train model
    model, train_metrics = train_model(X, y)

    # 7. Validate against Golden Set
    success, val_metrics = validate_against_golden_set(model, feature_cols)

    # 8. Save model
    if success:
        output_path = Path(MODEL_OUTPUT_PATH)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {MODEL_OUTPUT_PATH}")
    else:
        logger.warning("Model validation failed. Model not saved.")

    # Summary
    logger.info("=== Training Summary ===")
    logger.info(f"Features used: {feature_cols}")
    logger.info(f"VIF Scores: {vif_scores}")
    logger.info(f"Training Metrics: {train_metrics}")
    logger.info(f"Validation Metrics: {val_metrics}")
    logger.info(f"Validation Status: {'PASSED' if success else 'FAILED'}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())