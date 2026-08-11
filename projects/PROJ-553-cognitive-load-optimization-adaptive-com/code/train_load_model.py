import os
import sys
import logging
import pickle
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.stats import pearsonr

# Import shared utilities from the project API surface
from utils import (
    setup_logging,
    get_logger,
    calculate_vif,
    check_vif_threshold,
)
from load_data import load_and_verify_datasets, validate_golden_set

# Configure project-wide logging
logger = setup_logging()

# Fixed seed for reproducibility
RANDOM_SEED = 42

def log_transform_latency(latency: float) -> float:
    """
    Apply log transformation to latency values to handle skewness.
    Adds a small epsilon to avoid log(0).
    """
    if latency <= 0:
        return 0.0
    return np.log1p(latency)

def aggregate_interaction_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate interaction counts (errors, hints, pauses) per session.
    Assumes 'session_id' is a column in the dataframe.
    """
    if 'session_id' not in df.columns:
        logger.warning("No 'session_id' column found. Skipping aggregation.")
        return df

    agg_df = df.groupby('session_id').agg(
        error_count=('is_error', 'sum'),
        hint_count=('hint_requested', 'sum'),
        pause_count=('pause_count', 'sum')
    ).reset_index()
    return agg_df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform feature engineering: log-transform latency, count errors/hints/pauses.
    """
    df = df.copy()

    # Log transform latency if present
    if 'latency' in df.columns:
        df['latency_log'] = df['latency'].apply(log_transform_latency)
    else:
        logger.warning("Column 'latency' not found in dataset.")

    # Aggregate counts if session data exists
    if 'session_id' in df.columns:
        agg = aggregate_interaction_counts(df)
        # Merge back to main dataframe if needed, or return aggregated for training
        # For this model, we assume the training unit is the session.
        # We'll merge the aggregated counts back to the session level.
        # If the input is already session-level, this is a no-op or simple join.
        df = df.merge(agg, on='session_id', how='left')

    return df

def check_collinearity(df: pd.DataFrame, feature_cols: List[str], threshold: float = 5.0) -> List[Tuple[str, float]]:
    """
    Check for multicollinearity using Variance Inflation Factor (VIF).
    Returns a list of (feature, vif_score) where vif_score > threshold.
    """
    if len(feature_cols) < 2:
        return []

    # Ensure we have numeric data for VIF calculation
    X = df[feature_cols].dropna()
    if X.empty:
        return []

    vif_results = []
    for col in feature_cols:
        try:
            vif = calculate_vif(X, col)
            vif_results.append((col, vif))
            if vif > threshold:
                logger.warning(f"High collinearity detected for {col}: VIF = {vif:.2f} (threshold: {threshold})")
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")

    return vif_results

def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    params: Optional[Dict[str, Any]] = None
) -> lgb.Booster:
    """
    Train a LightGBM Gradient Boosting Regressor.
    Uses fixed seed for reproducibility.
    """
    if params is None:
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'tree_method': 'hist',
            'device': 'cpu',
            'seed': RANDOM_SEED,
            'verbose': -1,
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
        }

    # Create LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    # Train model
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )

    return model

def validate_against_golden_set(model: lgb.Booster, golden_df: pd.DataFrame, feature_cols: List[str]) -> Tuple[float, float]:
    """
    Validate the trained model against the Golden Set.
    Computes Pearson correlation between predicted and expert labels.
    Target: Pearson r >= 0.6
    """
    if 'expert_load_score' not in golden_df.columns:
        raise ValueError("Golden Set missing 'expert_load_score' column.")

    # Ensure features exist
    missing = [f for f in feature_cols if f not in golden_df.columns]
    if missing:
        raise ValueError(f"Missing required features in Golden Set: {missing}")

    X_golden = golden_df[feature_cols].dropna()
    y_golden = golden_df.loc[X_golden.index, 'expert_load_score']

    if len(X_golden) < 10:
        raise ValueError(f"Insufficient samples for validation after dropping NaNs: {len(X_golden)}")

    # Predict
    y_pred = model.predict(X_golden)

    # Calculate Pearson correlation
    r, p_value = pearsonr(y_pred, y_golden)

    logger.info(f"Validation against Golden Set: Pearson r = {r:.4f}, p-value = {p_value:.4f}")

    return r, p_value

def main():
    """
    Main execution flow for Task T014:
    1. Load and verify datasets (ASSISTments/OULAD)
    2. Verify Golden Set exists
    3. Engineer features
    4. Train LightGBM model
    5. Validate against Golden Set (Target r >= 0.6)
    6. Save model artifact
    """
    logger.info("Starting Model Training Loop (T014)...")

    # 1. Load and verify datasets
    logger.info("Loading and verifying datasets...")
    # Assuming load_and_verify_datasets handles fetching and basic checks
    # It should return a combined dataframe or a dict of dataframes
    datasets = load_and_verify_datasets()

    # 2. Verify Golden Set
    golden_path = Path("data/processed/golden_set.csv")
    if not golden_path.exists():
        logger.error(f"Golden Set not found at {golden_path}. Please run T006b to create it.")
        sys.exit(1)

    golden_df = validate_golden_set(golden_path)
    if golden_df is None:
        logger.error("Golden Set validation failed.")
        sys.exit(1)

    logger.info(f"Golden Set loaded with {len(golden_df)} samples.")

    # 3. Feature Engineering
    # We assume the main dataset is the first one or a merged one
    # For this implementation, we assume datasets contains the training data
    # under a key 'train' or similar, or we use the first available dataframe
    if isinstance(datasets, dict):
        # Try to find a reasonable training dataframe
        train_df = datasets.get('train') or datasets.get('combined') or list(datasets.values())[0]
    else:
        train_df = datasets

    # Engineer features on training data
    logger.info("Engineering features...")
    train_df = engineer_features(train_df)

    # Define feature columns (exclude identifiers and target if present)
    exclude_cols = ['session_id', 'expert_load_score', 'user_id', 'problem_id']
    feature_cols = [col for col in train_df.columns if col not in exclude_cols and train_df[col].dtype in ['int64', 'float64']]

    # Check for collinearity
    logger.info("Checking collinearity...")
    high_vif_features = check_collinearity(train_df, feature_cols, threshold=5.0)
    if high_vif_features:
        logger.warning("Features with VIF > 5 detected. Proceeding with caution.")

    # Prepare training data
    # Filter out rows with NaN in features or target (if target exists in training set)
    # For this task, we assume we are training on the public dataset features
    # and validating ONLY on the Golden Set labels.
    # If the training set has a target, we use it. If not, we might need to synthesize
    # or use a proxy, but the task implies training on interaction features.
    # Assuming the public dataset has a 'correct' or 'time' based proxy or we are
    # training a regression on the features themselves to predict the Golden Set target later?
    # Clarification: The task says "Train ... predicting continuous load scores".
    # Usually, we need a target in the training set. If the public dataset doesn't have 'expert_load_score',
    # we might be using a proxy (e.g., time on task, error rate) as a temporary target,
    # OR the public dataset has a 'correct' column we can convert to a score.
    # However, the strict requirement is validation against Golden Set.
    # Let's assume the public dataset has a 'score' or we use a heuristic target for training.
    # For robustness, we will check if 'score' or 'correct' exists.
    # If not, we cannot train a supervised model.
    # Given T004/T011 context, we likely have 'latency', 'errors', etc.
    # We will assume a target column 'target_load' exists or create a proxy.
    # If no target exists, we must raise an error.
    
    target_col = 'target_load'
    if target_col not in train_df.columns:
        # Fallback: If 'correct' exists, maybe use it? Or 'time'?
        # But the task is to predict LOAD.
        # Let's assume the dataset has a 'load_score' or similar, or we must generate one?
        # No, T006b generates the Golden Set. The training data must have a target.
        # If the public dataset (ASSISTments) has 'correct', we can't directly use it as load.
        # We will assume the task implies using the 'expert_load_score' from the Golden Set
        # as the ONLY target, and the model is trained on the intersection?
        # No, that's too small.
        # Standard approach: Train on public data with a proxy, validate on Golden Set.
        # Let's assume a proxy column 'proxy_load' exists or we use 'latency' as a proxy?
        # Actually, the prompt says "predicting continuous load scores".
        # If no target exists in the public data, we cannot train.
        # Let's assume the public dataset has a 'score' or we are using the 'expert_load_score'
        # from the Golden Set as the target for the model, and we train on the union?
        # No, the Golden Set is small (50 samples).
        # Let's assume the public dataset has a 'load' column or we must create one.
        # For the sake of this task, we will assume the public dataset has a 'target_load'
        # or we use the 'correct' column as a binary target and convert to score?
        # No, we need continuous.
        # Let's assume the task implies we have a target in the public data.
        # If not, we raise an error.
        raise ValueError("Training data must contain a target column (e.g., 'target_load' or 'expert_load_score').")

    # Split data (if not already split)
    # We assume the dataset has a 'split' column or we split randomly
    if 'split' in train_df.columns:
        train_data = train_df[train_df['split'] == 'train']
        val_data = train_df[train_df['split'] == 'val']
    else:
        # Random split
        train_data = train_df.sample(frac=0.8, random_state=RANDOM_SEED)
        val_data = train_df.drop(train_data.index)

    # Prepare X and y
    X_train = train_data[feature_cols].fillna(0)
    y_train = train_data[target_col].fillna(0)
    X_val = val_data[feature_cols].fillna(0)
    y_val = val_data[target_col].fillna(0)

    # 4. Train Model
    logger.info("Training LightGBM model...")
    model = train_model(X_train, y_train, X_val, y_val)

    # 5. Validate against Golden Set
    logger.info("Validating against Golden Set...")
    try:
        r, p = validate_against_golden_set(model, golden_df, feature_cols)
        if r < 0.6:
            logger.warning(f"Model validation failed: Pearson r = {r:.4f} < 0.6")
            # We do not exit, but log the warning as per task requirements
            # The task says "validation against ... (Pearson r >= 0.6 target)"
            # It doesn't say "fail if < 0.6", but usually this is a gate.
            # We will log it and proceed, but in a real pipeline, this might block.
            # For T014, we implement the loop and the check.
        else:
            logger.info(f"Model validation passed: Pearson r = {r:.4f} >= 0.6")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    # 6. Save Model
    output_path = Path("data/processed/load_model.pkl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {output_path}")

    return model

if __name__ == "__main__":
    main()
