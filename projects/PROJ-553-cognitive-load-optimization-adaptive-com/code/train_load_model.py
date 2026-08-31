import os
import sys
import logging
import pickle
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr

# Import from local utils
from utils import setup_logging, get_logger, calculate_vif, check_vif_threshold

# Ensure the directory containing this file is in the path for imports
# This is a safeguard if the script is run directly from the code directory
if os.path.basename(os.getcwd()) == 'code':
    sys.path.insert(0, os.getcwd())

# Constants
RANDOM_SEED = 42
TARGET_CORRELATION = 0.6
MODEL_SIZE_LIMIT_MB = 500
GOLDEN_SET_PATH = "data/processed/golden_set.csv"
MODEL_OUTPUT_PATH = "data/processed/load_model.pkl"
METRICS_OUTPUT_PATH = "data/processed/model_metrics.json"
TEMP_MODEL_PATH = "data/processed/temp_load_model.pkl"

def set_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def log_transform_latency(df: pd.DataFrame, latency_col: str = 'response_latency') -> pd.DataFrame:
    """Apply log transform to latency, handling zeros."""
    df = df.copy()
    if latency_col in df.columns:
        # Add small epsilon to avoid log(0)
        df[f'log_{latency_col}'] = np.log1p(df[latency_col].clip(lower=0))
    return df

def aggregate_interaction_counts(df: pd.DataFrame, session_id_col: str = 'session_id') -> pd.DataFrame:
    """Aggregate interaction counts (errors, hints, pauses) per session."""
    # Group by session and count specific features if they exist
    agg_dict = {}
    if 'is_error' in df.columns:
        agg_dict['error_count'] = ('is_error', 'sum')
    if 'hint_requested' in df.columns:
        agg_dict['hint_count'] = ('hint_requested', 'sum')
    if 'pause_duration' in df.columns:
        agg_dict['total_pause'] = ('pause_duration', 'sum')
        agg_dict['pause_count'] = ('pause_duration', 'count')

    if agg_dict:
        grouped = df.groupby(session_id_col).agg(**agg_dict)
        return grouped.reset_index()
    return pd.DataFrame()

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features for the model."""
    df = df.copy()
    
    # Log transform latency
    df = log_transform_latency(df, 'response_latency')
    
    # Aggregate counts if session data exists
    if 'session_id' in df.columns:
        agg_df = aggregate_interaction_counts(df)
        # Merge back if needed, or assume df is already session-level
        # For this implementation, we assume df is already at the interaction/session level
        # with pre-aggregated counts or we aggregate here.
        # Let's assume df has columns: 'error_count', 'hint_count', 'total_pause'
        pass
    
    # Ensure numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df = df[numeric_cols]
    
    return df

def check_collinearity(df: pd.DataFrame, threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """Calculate VIF and flag collinear predictors."""
    # Filter out target variable and non-numeric
    feature_cols = [c for c in df.columns if c != 'expert_load_score' and df[c].dtype in [np.int64, np.float64]]
    if len(feature_cols) < 2:
        return df, []

    vif_data = []
    for col in feature_cols:
        try:
            vif = calculate_vif(df, col, feature_cols)
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")

    flagged = [row['feature'] for row in vif_data if row['vif'] > threshold]
    logger = get_logger()
    if flagged:
        logger.warning(f"High collinearity detected (VIF > {threshold}) for: {flagged}")
    else:
        logger.info(f"No features with VIF > {threshold} detected.")

    return df, flagged

def ensure_golden_set_validity(path: str) -> pd.DataFrame:
    """Load and validate the golden set."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Golden set not found at {path}. Cannot proceed with training.")
    
    df = pd.read_csv(path)
    
    required_cols = ['expert_load_score']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Golden set missing required columns: {required_cols}")
    
    if df['expert_load_score'].isna().any():
        df = df.dropna(subset=['expert_load_score'])
        logging.warning("Dropped rows with NaN expert_load_score")
    
    if len(df) < 50:
        raise ValueError(f"Golden set has only {len(df)} rows. Need at least 50.")
    
    if not (df['expert_load_score'] >= 0).all() or not (df['expert_load_score'] <= 100).all():
        raise ValueError("expert_load_score must be between 0 and 100.")
    
    return df

def train_model(X: pd.DataFrame, y: pd.Series) -> lgb.Booster:
    """Train LightGBM model with fixed seed."""
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED
    )

    # Create datasets
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
        'seed': RANDOM_SEED,
        'force_col_wise': True
    }

    # Train
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[train_data, val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=0)]
    )

    return model

def validate_model(model: lgb.Booster, X: pd.DataFrame, y: pd.Series) -> float:
    """Validate model against Golden Set (Pearson r)."""
    y_pred = model.predict(X)
    r, p_value = pearsonr(y, y_pred)
    return r

def check_model_size(path: str, limit_mb: int = MODEL_SIZE_LIMIT_MB) -> bool:
    """Check if model file size is within limit."""
    size_bytes = os.path.getsize(path)
    size_mb = size_bytes / (1024 * 1024)
    if size_mb > limit_mb:
        raise ValueError(f"Model size {size_mb:.2f} MB exceeds limit of {limit_mb} MB.")
    return True

def save_model(model: lgb.Booster, path: str) -> None:
    """Save model to pickle file."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logging.info(f"Model saved to {path}")

def save_metrics(metrics: Dict[str, Any], path: str) -> None:
    """Save training metrics to JSON."""
    import json
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Metrics saved to {path}")

def main():
    """Main training loop for T017."""
    set_seed(RANDOM_SEED)
    logger = setup_logging()
    logger.info("Starting T017: Model Training Loop")

    # 1. Load and validate Golden Set
    logger.info(f"Loading Golden Set from {GOLDEN_SET_PATH}")
    try:
        golden_df = ensure_golden_set_validity(GOLDEN_SET_PATH)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)

    # 2. Feature Engineering
    # Assuming the golden set already has the necessary features (errors, hints, latency)
    # If not, we need to join with raw data. For T017, we assume T014/T016 prepared the data
    # or the golden set contains the engineered features.
    # Let's assume the CSV has columns: [session_id, error_count, hint_count, log_response_latency, expert_load_score]
    # We select numeric predictors
    feature_cols = [c for c in golden_df.columns if c != 'expert_load_score' and golden_df[c].dtype in [np.int64, np.float64, np.float32]]
    
    if len(feature_cols) == 0:
        logger.error("No numeric feature columns found in Golden Set.")
        sys.exit(1)

    X = golden_df[feature_cols]
    y = golden_df['expert_load_score']

    # 3. Collinearity Check (T016 requirement)
    X, flagged_cols = check_collinearity(golden_df[feature_cols + ['expert_load_score']])
    if flagged_cols:
        logger.warning(f"Features flagged for collinearity: {flagged_cols}. Proceeding with caution.")

    # 4. Train Model (T015 requirement)
    logger.info("Training LightGBM model...")
    try:
        model = train_model(X, y)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

    # 5. Validation (Pearson r >= 0.6)
    logger.info("Validating model performance...")
    r_score = validate_model(model, X, y)
    logger.info(f"Pearson Correlation (r): {r_score:.4f}")

    if r_score < TARGET_CORRELATION:
        error_msg = f"Validation failed: Pearson r ({r_score:.4f}) < {TARGET_CORRELATION}. Model not saved."
        logger.error(error_msg)
        # Do not save the model if validation fails
        sys.exit(1)

    # 6. Save to temporary location first (as per T017 description)
    logger.info(f"Saving model to temporary location: {TEMP_MODEL_PATH}")
    save_model(model, TEMP_MODEL_PATH)

    # 7. Check size
    check_model_size(TEMP_MODEL_PATH)

    # 8. Save final metrics
    metrics = {
        'pearson_r': r_score,
        'target_threshold': TARGET_CORRELATION,
        'n_samples': len(X),
        'n_features': len(feature_cols),
        'random_seed': RANDOM_SEED,
        'flagged_collinear_features': flagged_cols
    }
    save_metrics(metrics, METRICS_OUTPUT_PATH)

    # 9. Move to final location (T015/18 requirement)
    final_path = Path(MODEL_OUTPUT_PATH)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(TEMP_MODEL_PATH, MODEL_OUTPUT_PATH)
    logger.info(f"Model successfully validated and moved to {MODEL_OUTPUT_PATH}")

    logger.info("T017 Completed Successfully")

if __name__ == "__main__":
    main()
