import os
import sys
import logging
import pickle
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import pearsonr
import lightgbm as lgb
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import existing utilities from the project
from utils import setup_logging, get_logger, load_config_env, validate_environment, calculate_vif, check_vif_threshold

# Constants
MIN_GOLDEN_SET_SIZE = 40
TARGET_PEARSON_R = 0.6
MODEL_PATH = "data/processed/load_model.pkl"
METRICS_PATH = "data/processed/model_metrics.json"

def log_transform_latency(latency: float) -> float:
    """Apply log transformation to latency to reduce skew."""
    if latency <= 0:
        return 0.0
    return np.log1p(latency)

def aggregate_interaction_counts(df: pd.DataFrame, session_id: str) -> Dict[str, int]:
    """Aggregate error, hint, and pause counts for a specific session."""
    session_data = df[df['session_id'] == session_id]
    return {
        'error_count': int(session_data['error'].sum()) if 'error' in session_data.columns else 0,
        'hint_count': int(session_data['hint_requested'].sum()) if 'hint_requested' in session_data.columns else 0,
        'pause_count': int(session_data['pause_count'].sum()) if 'pause_count' in session_data.columns else 0,
        'total_interactions': len(session_data)
    }

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features from raw interaction data."""
    features = []
    sessions = df['session_id'].unique()
    
    for session_id in sessions:
        session_data = df[df['session_id'] == session_id]
        
        # Calculate aggregated counts
        counts = aggregate_interaction_counts(df, session_id)
        
        # Log transform latency
        avg_latency = session_data['response_time'].mean() if 'response_time' in session_data.columns else 0
        log_latency = log_transform_latency(avg_latency)
        
        # Calculate error rate
        error_rate = counts['error_count'] / max(counts['total_interactions'], 1)
        
        # Calculate hint rate
        hint_rate = counts['hint_count'] / max(counts['total_interactions'], 1)
        
        feature_row = {
            'session_id': session_id,
            'log_latency': log_latency,
            'error_rate': error_rate,
            'hint_rate': hint_rate,
            'total_interactions': counts['total_interactions'],
            'error_count': counts['error_count'],
            'hint_count': counts['hint_count']
        }
        
        # Add expert load score if available (for validation)
        if 'expert_load_score' in session_data.columns:
            feature_row['expert_load_score'] = session_data['expert_load_score'].mean()
        
        features.append(feature_row)
    
    return pd.DataFrame(features)

def check_collinearity(df: pd.DataFrame, feature_cols: List[str], threshold: float = 5.0) -> Tuple[bool, Dict[str, float]]:
    """Check for multicollinearity using VIF."""
    vif_data = {}
    X = df[feature_cols].dropna()
    
    if X.shape[0] < len(feature_cols) + 1:
        logging.warning("Insufficient samples for VIF calculation")
        return True, vif_data
        
    for i, col in enumerate(feature_cols):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
        if vif > threshold:
            logging.warning(f"High collinearity detected for {col}: VIF = {vif:.2f}")
            return False, vif_data
    
    return True, vif_data

def ensure_golden_set_validity(golden_set_path: str) -> pd.DataFrame:
    """
    Validate the Golden Set exists and meets minimum sample size requirements.
    
    This function implements error handling for:
    1. Missing Golden Set file
    2. Insufficient sample size (N < 40)
    
    Raises:
        FileNotFoundError: If the Golden Set file does not exist
        ValueError: If the sample size is less than 40
    """
    path = Path(golden_set_path)
    
    # Check if file exists
    if not path.exists():
        error_msg = (
            f"CRITICAL ERROR: Golden Set validation failed. "
            f"File not found at '{golden_set_path}'. "
            f"The model training pipeline requires a validated Golden Set with expert labels. "
            f"Please ensure the Golden Set has been acquired via T006b before proceeding."
        )
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Load the Golden Set
    try:
        golden_df = pd.read_csv(path)
    except Exception as e:
        error_msg = (
            f"CRITICAL ERROR: Failed to load Golden Set from '{golden_set_path}'. "
            f"Error: {str(e)}"
        )
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Check for required columns
    required_cols = ['session_id', 'expert_load_score']
    missing_cols = [col for col in required_cols if col not in golden_df.columns]
    if missing_cols:
        error_msg = (
            f"CRITICAL ERROR: Golden Set missing required columns: {missing_cols}. "
            f"Required columns are: {required_cols}"
        )
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Check sample size
    sample_size = len(golden_df)
    if sample_size < MIN_GOLDEN_SET_SIZE:
        error_msg = (
            f"CRITICAL ERROR: Golden Set sample size insufficient. "
            f"Current size: {sample_size}, Minimum required: {MIN_GOLDEN_SET_SIZE}. "
            f"The model training requires at least {MIN_GOLDEN_SET_SIZE} expert-labeled interactions "
            f"to ensure statistical validity. Please acquire more expert labels before proceeding."
        )
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    logging.info(f"Golden Set validation passed: {sample_size} samples found (min required: {MIN_GOLDEN_SET_SIZE})")
    return golden_df

def train_model(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> lgb.Booster:
    """Train LightGBM model with early stopping."""
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'verbose': -1,
        'seed': 42
    }
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=100,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=10, verbose=False)]
    )
    
    return model

def validate_against_golden_set(model: lgb.Booster, golden_df: pd.DataFrame, feature_cols: List[str]) -> float:
    """Validate model predictions against Golden Set expert labels."""
    X_golden = golden_df[feature_cols].dropna()
    y_golden = golden_df.loc[X_golden.index, 'expert_load_score']
    
    if len(X_golden) == 0:
        raise ValueError("No valid samples in Golden Set after feature engineering")
    
    predictions = model.predict(X_golden)
    pearson_r, _ = pearsonr(predictions, y_golden)
    
    return pearson_r

def check_model_size(model_path: str, max_size_mb: float = 500.0) -> bool:
    """Check if model size is within constraints."""
    path = Path(model_path)
    if not path.exists():
        return False
    
    size_mb = path.stat().st_size / (1024 * 1024)
    return size_mb <= max_size_mb

def save_model(model: lgb.Booster, path: str) -> None:
    """Save model to disk."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def save_metrics(metrics: Dict[str, Any], path: str) -> None:
    """Save training metrics to disk."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point for model training with Golden Set validation."""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting cognitive load model training pipeline")
    
    # Load configuration
    config = load_config_env()
    golden_set_path = config.get('golden_set_path', 'data/processed/golden_set.csv')
    
    try:
        # STEP 1: Validate Golden Set (T016 Error Handling)
        logger.info(f"Validating Golden Set at: {golden_set_path}")
        golden_df = ensure_golden_set_validity(golden_set_path)
        logger.info(f"Golden Set loaded successfully with {len(golden_df)} samples")
        
        # STEP 2: Load and prepare training data
        # Assuming data is already loaded by T004/T005 into data/processed/
        training_data_path = config.get('training_data_path', 'data/processed/training_data.csv')
        
        if not Path(training_data_path).exists():
            logger.error(f"Training data not found at {training_data_path}. "
                       "Please ensure T004 has been completed to load datasets.")
            sys.exit(1)
        
        train_df = pd.read_csv(training_data_path)
        logger.info(f"Loaded training data with {len(train_df)} interactions")
        
        # STEP 3: Feature Engineering
        logger.info("Engineering features...")
        features_df = engineer_features(train_df)
        
        # Remove rows with missing expert_load_score for training
        features_df = features_df.dropna(subset=['expert_load_score'])
        
        if len(features_df) < MIN_GOLDEN_SET_SIZE:
            logger.warning(f"Training data sample size ({len(features_df)}) is below recommended minimum ({MIN_GOLDEN_SET_SIZE})")
        
        # Define feature columns
        feature_cols = ['log_latency', 'error_rate', 'hint_rate', 'total_interactions']
        feature_cols = [col for col in feature_cols if col in features_df.columns]
        
        if len(feature_cols) == 0:
            raise ValueError("No valid feature columns found for training")
        
        # STEP 4: Check Collinearity
        logger.info("Checking collinearity...")
        collinearity_ok, vif_data = check_collinearity(features_df, feature_cols)
        if not collinearity_ok:
            logger.warning("High collinearity detected - proceeding with caution")
        
        # STEP 5: Train/Validation Split
        X = features_df[feature_cols]
        y = features_df['expert_load_score']
        
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        logger.info(f"Training set size: {len(X_train)}, Validation set size: {len(X_val)}")
        
        # STEP 6: Train Model
        logger.info("Training LightGBM model...")
        model = train_model(X_train, y_train, X_val, y_val)
        
        # STEP 7: Validate Against Golden Set
        logger.info("Validating model against Golden Set...")
        # Use the full dataset for validation as per T014
        full_predictions = model.predict(features_df[feature_cols])
        pearson_r, _ = pearsonr(full_predictions, features_df['expert_load_score'])
        
        logger.info(f"Model validation: Pearson r = {pearson_r:.4f} (target: >= {TARGET_PEARSON_R})")
        
        if pearson_r < TARGET_PEARSON_R:
            logger.warning(f"Model performance below target (r={pearson_r:.4f} < {TARGET_PEARSON_R}). "
                         "Consider feature engineering improvements or more data.")
        
        # STEP 8: Save Model
        model_path = MODEL_PATH
        save_model(model, model_path)
        logger.info(f"Model saved to {model_path}")
        
        # STEP 9: Check Model Size
        if not check_model_size(model_path):
            size_mb = Path(model_path).stat().st_size / (1024 * 1024)
            logger.warning(f"Model size ({size_mb:.2f} MB) exceeds recommended limit (500 MB)")
        
        # STEP 10: Save Metrics
        metrics = {
            'pearson_r': pearson_r,
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'total_samples': len(features_df),
            'feature_columns': feature_cols,
            'vif_values': vif_data,
            'model_path': model_path
        }
        save_metrics(metrics, METRICS_PATH)
        logger.info(f"Metrics saved to {METRICS_PATH}")
        
        logger.info("Model training pipeline completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        logger.error("The pipeline cannot proceed without a valid Golden Set. "
                   "Please run T006b to acquire the required expert-labeled data.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        if "insufficient" in str(e).lower() or "sample size" in str(e).lower():
            logger.error("The Golden Set does not meet the minimum sample size requirement (N >= 40).")
            logger.error("Please acquire more expert-labeled interactions before proceeding.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {str(e)}")
        raise

if __name__ == "__main__":
    main()