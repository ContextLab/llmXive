"""
Cognitive Load Estimation Model Training

This module implements the training pipeline for predicting cognitive load scores
based on behavioral proxies (latency, errors, hints) validated against expert labels.

CRITICAL DESIGN PRINCIPLE:
--------------------------
This model uses **behavioral proxies** (latency, errors, hints) as INPUT features.
Validation is STRICTLY against the external **Golden Set** expert labels.

This separation ensures no conflation of input features with validation targets,
directly addressing the "illusion of competence" critique. The model predicts
load based on observable behavior, not self-reported ease or fluency metrics,
and is validated against independent expert judgment to ensure the predictions
reflect actual cognitive demand rather than perceived ease.

Dependencies:
- pandas, numpy, lightgbm, sklearn
- code/utils.py (for VIF calculation)
"""

import os
import sys
import logging
import pickle
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr

# Import utilities from sibling module
try:
    from utils import calculate_vif, check_vif_threshold, get_logger
except ImportError:
    # Fallback for direct execution context
    sys.path.insert(0, str(Path(__file__).parent))
    from utils import calculate_vif, check_vif_threshold, get_logger

# Constants
RANDOM_SEED = 42
TARGET_PEARSON_R = 0.6
VIF_THRESHOLD = 5.0
MODEL_PATH = Path("data/processed/load_model.pkl")
MODEL_LOW_CONF_PATH = Path("data/processed/load_model_low_confidence.pkl")
METRICS_PATH = Path("data/processed/model_metrics.json")
GOLDEN_SET_PATH = Path("data/processed/golden_set.csv")

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def log_transform_latency(latency_values: pd.Series) -> pd.Series:
    """
    Apply log transformation to latency features to handle skewness.
    Adds a small epsilon to avoid log(0).
    """
    epsilon = 1e-6
    return np.log1p(latency_values + epsilon)

def aggregate_interaction_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate interaction counts per session/user.
    Counts errors, hints, and pauses.
    """
    # Assuming 'session_id' exists, if not use a generic index
    if 'session_id' not in df.columns:
        df['session_id'] = df.index

    agg_df = df.groupby('session_id').agg({
        'error_count': 'sum',
        'hint_count': 'sum',
        'pause_count': 'sum'
    }).reset_index()
    
    # Fill NaN with 0
    agg_df = agg_df.fillna(0)
    return agg_df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature Engineering Pipeline.
    
    TRANSFORMS raw interaction data into predictive features.
    IMPORTANT: These features are BEHAVIORAL PROXIES only.
    They are NOT the validation target (expert_load_score).
    
    Features created:
    - log_latency: Log-transformed response time
    - error_rate: Normalized error count
    - hint_frequency: Normalized hint request rate
    - pause_ratio: Ratio of pause time to total time
    """
    df = df.copy()
    
    # Log transform latency if present
    if 'latency' in df.columns:
        df['log_latency'] = log_transform_latency(df['latency'])
    elif 'response_time' in df.columns:
        df['log_latency'] = log_transform_latency(df['response_time'])
    else:
        # Fallback or raise warning if no latency feature found
        logging.warning("No latency feature found. Using dummy column.")
        df['log_latency'] = 0.0

    # Aggregate counts if not already aggregated
    # Assuming raw data might need aggregation or counts are already present
    if 'error_count' not in df.columns:
        df['error_count'] = 0
    if 'hint_count' not in df.columns:
        df['hint_count'] = 0
    if 'pause_count' not in df.columns:
        df['pause_count'] = 0

    # Normalize counts (simple z-score or min-max if data allows)
    # For robustness, just use raw counts if normalization causes issues
    df['error_rate'] = df['error_count']
    df['hint_frequency'] = df['hint_count']
    
    # Calculate pause ratio if duration data exists
    if 'total_duration' in df.columns and 'pause_count' in df.columns:
        df['pause_ratio'] = df['pause_count'] / (df['total_duration'] + 1e-6)
    else:
        df['pause_ratio'] = 0.0

    return df

def check_collinearity(df: pd.DataFrame, target_col: str = 'expert_load_score') -> Tuple[bool, Dict[str, float]]:
    """
    Check for multicollinearity using VIF.
    
    Returns:
        Tuple of (is_safe, vif_scores)
        is_safe: True if all VIF <= VIF_THRESHOLD
    """
    feature_cols = [col for col in df.columns if col != target_col]
    if not feature_cols:
        return True, {}

    vif_scores = {}
    is_safe = True
    
    # Ensure no NaNs in features for VIF calculation
    clean_df = df[feature_cols].dropna()
    if clean_df.empty:
        logging.warning("Insufficient data for VIF calculation.")
        return True, {}

    for col in feature_cols:
        try:
            vif = calculate_vif(clean_df, col)
            vif_scores[col] = vif
            if vif > VIF_THRESHOLD:
                is_safe = False
                logging.warning(f"High collinearity detected for {col}: VIF = {vif:.2f}")
        except Exception as e:
            logging.error(f"Error calculating VIF for {col}: {e}")
            vif_scores[col] = float('inf')
            is_safe = False

    return is_safe, vif_scores

def ensure_golden_set_validity(path: Path = GOLDEN_SET_PATH) -> pd.DataFrame:
    """
    Load and validate the Golden Set.
    
    CRITICAL: This function ensures the validation data (expert labels)
    is distinct from the input features used for training.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Golden Set file not found at {path}. "
            "The pipeline cannot proceed without external expert labels. "
            "Please complete the manual labeling process (T007g)."
        )

    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ['interaction_id', 'expert_load_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Golden Set missing required columns: {missing_cols}")

    # Validate score range
    if not df['expert_load_score'].between(0, 100).all():
        logging.warning("Some expert_load_score values are outside 0-100 range. Clipping...")
        df['expert_load_score'] = df['expert_load_score'].clip(0, 100)

    if len(df) < 50:
        logging.warning(f"Golden Set has only {len(df)} rows. Minimum 50 recommended.")

    return df

def load_validation_config() -> Dict[str, Any]:
    """Load validation configuration if exists, otherwise return defaults."""
    # Placeholder for future config loading
    return {
        "target_pearson_r": TARGET_PEARSON_R,
        "vif_threshold": VIF_THRESHOLD
    }

def train_model(X: pd.DataFrame, y: pd.Series, config: Dict[str, Any]) -> Tuple[lgb.Booster, Dict[str, float]]:
    """
    Train the Gradient Boosting Regressor (LightGBM).
    
    Args:
        X: Feature matrix (behavioral proxies)
        y: Target vector (expert_load_score from Golden Set)
        config: Validation configuration
    
    Returns:
        Trained model and metrics dictionary
    """
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )

    # Prepare LightGBM datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

    # Parameters
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'device': 'cpu',  # Enforce CPU as per constraints
        'force_col_wise': True
    }

    # Train
    model = lgb.train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
    )

    # Predict and evaluate
    y_pred = model.predict(X_val, num_iteration=model.best_iteration)
    
    # Calculate metrics
    mse = mean_squared_error(y_val, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_val, y_pred)
    
    # Pearson correlation (Critical for this task)
    try:
        pearson_r, _ = pearsonr(y_val, y_pred)
    except Exception as e:
        logging.error(f"Pearson correlation failed: {e}")
        pearson_r = 0.0

    metrics = {
        'rmse': float(rmse),
        'r2': float(r2),
        'pearson_r': float(pearson_r),
        'val_size': len(y_val),
        'train_size': len(y_train)
    }

    return model, metrics

def validate_model(metrics: Dict[str, float], config: Dict[str, Any]) -> bool:
    """
    Validate model against target Pearson r.
    
    Returns True if r >= TARGET_PEARSON_R, False otherwise.
    """
    return metrics['pearson_r'] >= config['target_pearson_r']

def check_model_size(path: Path, max_size_mb: int = 500) -> bool:
    """Check if model file size is within limits."""
    if not path.exists():
        return False
    size_mb = path.stat().st_size / (1024 * 1024)
    return size_mb <= max_size_mb

def save_model(model: lgb.Booster, path: Path) -> None:
    """Save the trained model."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logging.info(f"Model saved to {path}")

def save_metrics(metrics: Dict[str, float], path: Path) -> None:
    """Save metrics to JSON."""
    import json
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Metrics saved to {path}")

def main():
    """Main entry point for training."""
    # Setup logging
    logger = get_logger(__name__)
    logger.info("Starting Cognitive Load Model Training")
    
    set_seed()
    config = load_validation_config()

    # 1. Load Golden Set (Validation Target)
    logger.info(f"Loading Golden Set from {GOLDEN_SET_PATH}")
    golden_df = ensure_golden_set_validity(GOLDEN_SET_PATH)

    # 2. Load Feature Data (Behavioral Proxies)
    # Assuming load_data.py has already processed data into data/processed/
    # We look for a processed features file or derive from raw
    features_path = Path("data/processed/features.csv")
    if not features_path.exists():
        # Fallback: try to load from raw if features not pre-computed
        # In a real pipeline, this would be a separate step or integrated
        logger.warning("Features file not found. Attempting to load raw data...")
        # Placeholder: In a real scenario, we'd load the raw dataset here
        # For this task, we assume the pipeline has produced features
        raise FileNotFoundError("Features file not found. Ensure T014 has run.")
    
    raw_df = pd.read_csv(features_path)
    
    # Merge with Golden Set to align targets
    # Assuming 'interaction_id' is the key
    if 'interaction_id' not in raw_df.columns:
        raw_df['interaction_id'] = raw_df.index
    
    merged_df = pd.merge(raw_df, golden_df[['interaction_id', 'expert_load_score']], 
                         on='interaction_id', how='inner')
    
    if merged_df.empty:
        raise ValueError("No matching data between features and Golden Set.")
    
    logger.info(f"Merged dataset size: {len(merged_df)}")

    # 3. Feature Engineering
    logger.info("Engineering features (behavioral proxies)...")
    engineered_df = engineer_features(merged_df)

    # 4. Check Collinearity
    logger.info("Checking collinearity (VIF)...")
    is_safe, vif_scores = check_collinearity(engineered_df, target_col='expert_load_score')
    if not is_safe:
        logger.warning("High collinearity detected. Proceeding with caution.")
        for col, vif in vif_scores.items():
            if vif > VIF_THRESHOLD:
                logger.warning(f"  - {col}: VIF={vif:.2f}")

    # 5. Prepare Training Data
    feature_cols = [c for c in engineered_df.columns if c not in ['interaction_id', 'expert_load_score']]
    X = engineered_df[feature_cols]
    y = engineered_df['expert_load_score']

    # Handle missing values
    X = X.fillna(0)

    # 6. Train Model
    logger.info("Training LightGBM model...")
    model, metrics = train_model(X, y, config)

    # 7. Validate and Save
    is_valid = validate_model(metrics, config)
    logger.info(f"Model Validation - Pearson r: {metrics['pearson_r']:.4f} (Target: {config['target_pearson_r']})")
    logger.info(f"Validation Status: {'PASSED' if is_valid else 'LOW CONFIDENCE'}")

    # Save metrics
    save_metrics(metrics, METRICS_PATH)

    # Save model
    if is_valid:
        save_path = MODEL_PATH
        if not check_model_size(save_path):
            logger.warning("Model size exceeds limit. Saving as low confidence anyway.")
            # We still save, but log the warning
        save_model(model, save_path)
    else:
        save_path = MODEL_LOW_CONF_PATH
        save_model(model, save_path)
        logger.warning("Model confidence low. Saved to low confidence path.")

    logger.info("Training complete.")
    return metrics

if __name__ == "__main__":
    main()