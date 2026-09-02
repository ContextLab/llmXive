import os
import sys
import logging
import pickle
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from scipy.stats import pearsonr
import lightgbm as lgb
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Local imports based on API surface
from utils import calculate_vif, get_logger, load_config_env
from load_data import load_and_verify_datasets, validate_golden_set

# Configure logging
logger = get_logger(__name__)

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'lgb' in sys.modules:
        lgb.seed = seed

def log_transform_latency(df: pd.DataFrame, latency_col: str) -> pd.DataFrame:
    """Apply log transform to latency features to handle skewness."""
    if latency_col not in df.columns:
        raise ValueError(f"Latency column '{latency_col}' not found in dataframe.")
    
    # Handle non-positive values by adding 1 or filtering
    df[latency_col] = df[latency_col].apply(lambda x: np.log1p(x) if x > 0 else 0)
    return df

def aggregate_interaction_counts(df: pd.DataFrame, session_col: str = 'session_id') -> pd.DataFrame:
    """Aggregate interaction counts (errors, hints, pauses) per session."""
    # Assuming standard column names based on T014 context
    count_cols = [c for c in df.columns if any(k in c.lower() for k in ['error', 'hint', 'pause', 'attempt'])]
    
    if not count_cols:
        logger.warning("No interaction count columns found. Returning dataframe as-is.")
        return df

    agg_df = df.groupby(session_col)[count_cols].sum().reset_index()
    return agg_df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform feature engineering:
    1. Log transform latency.
    2. Aggregate counts.
    3. Create derived features if possible.
    """
    # Identify latency column
    latency_candidates = ['response_time', 'latency', 'duration_ms', 'time_spent']
    latency_col = None
    for cand in latency_candidates:
        if cand in df.columns:
            latency_col = cand
            break
    
    if latency_col:
        df = log_transform_latency(df, latency_col)
        logger.info(f"Applied log transform to {latency_col}")
    else:
        logger.warning("No latency column found for transformation.")

    # Aggregate counts
    df = aggregate_interaction_counts(df)
    
    return df

def check_collinearity(df: pd.DataFrame, feature_cols: list) -> Tuple[Dict[str, float], bool]:
    """
    Calculate VIF for features. Returns dict of VIF scores and boolean (True if VIF > 5).
    """
    vif_data = {}
    max_vif = 0
    high_vif = False

    # Add constant for VIF calculation
    X = df[feature_cols].dropna()
    if X.empty:
        return vif_data, False

    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        X_const = sm.add_constant(X)
        for i, col in enumerate(X.columns):
            vif = variance_inflation_factor(X_const.values, i+1) # +1 because of const
            vif_data[col] = vif
            if vif > max_vif:
                max_vif = vif
            if vif > 5:
                high_vif = True
        logger.info(f"Max VIF observed: {max_vif:.2f}")
    except Exception as e:
        logger.warning(f"Could not compute VIF: {e}")
    
    return vif_data, high_vif

def ensure_golden_set_validity(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure the golden set has valid target values."""
    # Check for target column
    if 'expert_load_score' not in df.columns:
        raise ValueError("Golden set must contain 'expert_load_score' column.")
    
    # Filter out NaN or out-of-range values
    valid_mask = df['expert_load_score'].notna() & (df['expert_load_score'] >= 0) & (df['expert_load_score'] <= 100)
    cleaned_df = df[valid_mask].copy()
    
    if len(cleaned_df) < 50:
        raise ValueError(f"Golden set has only {len(cleaned_df)} valid rows. Need >= 50.")
    
    return cleaned_df

def load_validation_config() -> Tuple[str, str]:
    """
    Reads validation_source.txt to determine the validation file path.
    Returns (source_type, file_path).
    """
    source_file = Path("data/processed/validation_source.txt")
    if not source_file.exists():
        raise FileNotFoundError("validation_source.txt not found. Run T007c first.")
    
    source_type = source_file.read_text().strip()
    
    if source_type == "golden_set":
        data_path = "data/processed/golden_set.csv"
    elif source_type == "public_self_report":
        # T007c creates this file if public self-reports are used
        data_path = "data/processed/golden_set.csv" 
    else:
        raise ValueError(f"Unknown validation source type: {source_type}")
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Validation data file {data_path} not found.")
    
    return source_type, data_path

def train_model(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> lgb.Booster:
    """Train LightGBM model with specified parameters."""
    set_seed(42)
    
    # Define parameters
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'tree_method': 'hist', # Explicitly requested
        'device': 'cpu',       # Explicitly requested
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1
    }
    
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1000,
        valid_sets=[val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=100)]
    )
    
    return model

def validate_model(model: lgb.Booster, X_val: pd.DataFrame, y_val: pd.Series) -> float:
    """
    Validate model against the available data.
    Returns Pearson correlation coefficient (r).
    Raises ValueError if r < 0.6.
    """
    preds = model.predict(X_val)
    r, p_value = pearsonr(y_val, preds)
    
    logger.info(f"Validation Pearson r: {r:.4f} (p-value: {p_value:.4f})")
    
    if r < 0.6:
        error_msg = f"Model validation failed: Pearson r ({r:.4f}) is below threshold (0.6). Halting pipeline."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Model validation passed.")
    return r

def check_model_size(path: str, max_mb: int = 500) -> bool:
    """Check if model file size is within limits."""
    size_bytes = os.path.getsize(path)
    size_mb = size_bytes / (1024 * 1024)
    logger.info(f"Model size: {size_mb:.2f} MB")
    if size_mb > max_mb:
        raise ValueError(f"Model size ({size_mb:.2f} MB) exceeds limit ({max_mb} MB).")
    return True

def save_model(model: lgb.Booster, path: str) -> None:
    """Save model to disk."""
    with open(path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {path}")

def save_metrics(metrics: Dict[str, Any], path: str) -> None:
    """Save metrics to JSON."""
    import json
    with open(path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {path}")

def main():
    """Main execution pipeline for T015."""
    logger.info("Starting T015: Gradient Boosting Regressor Pipeline")
    
    # 1. Load Validation Config
    source_type, data_path = load_validation_config()
    logger.info(f"Using validation source: {source_type} from {data_path}")
    
    # 2. Load Data
    # T004 ensures data is in data/processed/dataset.csv or similar
    # We assume the golden set contains the necessary features + target
    df = pd.read_csv(data_path)
    
    # 3. Ensure Validity
    df = ensure_golden_set_validity(df)
    
    # 4. Feature Engineering
    df = engineer_features(df)
    
    # Identify features and target
    target_col = 'expert_load_score'
    feature_cols = [c for c in df.columns if c != target_col]
    
    if not feature_cols:
        raise ValueError("No features found for training after engineering.")
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    if len(X) < 50:
        raise ValueError("Insufficient data for training after cleaning.")
    
    # 5. Split Data
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 6. Check Collinearity (T016 dependency)
    vif_scores, high_vif = check_collinearity(X_train, feature_cols)
    if high_vif:
        logger.warning("High collinearity detected (VIF > 5). Proceeding with caution.")
    
    # 7. Train Model
    model = train_model(X_train, y_train, X_val, y_val)
    
    # 8. Validate Model (Target r >= 0.6)
    r_score = validate_model(model, X_val, y_val)
    
    # 9. Save Model
    model_path = "data/processed/load_model.pkl"
    save_model(model, model_path)
    
    # 10. Check Size
    check_model_size(model_path)
    
    # 11. Save Metrics
    metrics = {
        "pearson_r": r_score,
        "validation_source": source_type,
        "num_features": len(feature_cols),
        "train_size": len(X_train),
        "val_size": len(X_val)
    }
    save_metrics(metrics, "data/processed/model_metrics.json")
    
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()