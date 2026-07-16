import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import joblib

# Project-relative imports based on provided API surface
from utils import set_random_seed, setup_logging
from error_handling import exit_on_insufficiency
from preprocess import load_parsed_data
from config.threshold_config import get_r2_threshold, get_threshold_justification

# Constants
RANDOM_SEED = 42
TRAIN_RATIO = 0.7
VAL_RATIO = 0.15
TEST_RATIO = 0.15
MIN_RECORDS = 500

# Setup logging
logger = setup_logging("train")

def load_and_prepare_data() -> pd.DataFrame:
    """
    Load the cleaned dataset from the preprocessing step.
    Ensures the dataset meets the minimum record requirement.
    """
    input_path = Path("data/processed/cleaned_dataset.parquet")
    
    if not input_path.exists():
        logger.error(f"Cleaned dataset not found at {input_path}. Run preprocess.py first.")
        sys.exit(1)
    
    df = pd.read_parquet(input_path)
    
    # Verify required columns exist
    required_cols = ['diffusivity', 'misorientation_angle', 'sigma_value', 
                     'boundary_plane_normal', 'temperature', 'composition',
                     'boundary_width', 'excess_volume', 'simulation_method', 'potential_id']
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns in dataset: {missing}")
        sys.exit(1)
    
    # Drop rows with any NaN in required columns to ensure clean training
    df = df.dropna(subset=required_cols)
    
    if len(df) < MIN_RECORDS:
        logger.error(f"Data Insufficiency: Retrieved {len(df)} < {MIN_RECORDS} valid records after cleaning.")
        exit_on_insufficiency(len(df), MIN_RECORDS)
    
    logger.info(f"Loaded {len(df)} valid records for training.")
    return df

def split_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a 70/15/15 split: train, validation, test.
    """
    # Separate features and target
    # Assuming 'diffusivity' is the target
    target_col = 'diffusivity'
    feature_cols = [col for col in df.columns if col != target_col]
    
    X = df[feature_cols]
    y = df[target_col]
    
    # First split: 70% train, 30% temp (val + test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(1 - TRAIN_RATIO), random_state=RANDOM_SEED, stratify=None
    )
    
    # Second split: from temp, split into 50% val, 50% test (relative to temp)
    # 0.5 * 0.3 = 0.15 of total
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=RANDOM_SEED, stratify=None
    )
    
    # Reconstruct dataframes
    train_df = X_train.copy()
    train_df[target_col] = y_train
    
    val_df = X_val.copy()
    val_df[target_col] = y_val
    
    test_df = X_test.copy()
    test_df[target_col] = y_test
    
    logger.info(f"Split complete: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df

def tune_hyperparameters(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> XGBRegressor:
    """
    Execute RandomizedSearchCV (k=5) for XGBoost hyperparameter tuning.
    Search space:
      max_depth: [3, 10]
      learning_rate: [0.01, 0.3]
      n_estimators: [50, 300]
    Scoring: r2
    """
    param_dist = {
        'max_depth': np.random.randint(3, 11),
        'learning_rate': np.random.uniform(0.01, 0.3),
        'n_estimators': np.random.randint(50, 301),
        'subsample': np.random.uniform(0.8, 1.0),
        'colsample_bytree': np.random.uniform(0.8, 1.0),
        'gamma': np.random.uniform(0, 1),
        'reg_alpha': np.random.uniform(0, 1),
        'reg_lambda': np.random.uniform(0, 1)
    }
    
    # We need to fix the distribution types for RandomizedSearchCV
    # max_depth is int, others are float
    # Re-define properly for RandomizedSearchCV
    param_distributions = {
        'max_depth': np.random.randint(3, 11, size=50), # 50 samples
        'learning_rate': np.random.uniform(0.01, 0.3, size=50),
        'n_estimators': np.random.randint(50, 301, size=50),
        'subsample': np.random.uniform(0.8, 1.0, size=50),
        'colsample_bytree': np.random.uniform(0.8, 1.0, size=50),
        'gamma': np.random.uniform(0, 1, size=50),
        'reg_alpha': np.random.uniform(0, 1, size=50),
        'reg_lambda': np.random.uniform(0, 1, size=50)
    }
    
    # Actually, RandomizedSearchCV expects distributions, not arrays
    # Let's use proper distributions
    from scipy.stats import randint, uniform
    
    param_distributions = {
        'max_depth': randint(3, 11),
        'learning_rate': uniform(0.01, 0.29), # 0.01 to 0.3
        'n_estimators': randint(50, 301),
        'subsample': uniform(0.8, 0.2),
        'colsample_bytree': uniform(0.8, 0.2),
        'gamma': uniform(0, 1),
        'reg_alpha': uniform(0, 1),
        'reg_lambda': uniform(0, 1)
    }

    base_model = XGBRegressor(
        objective='reg:squarederror',
        random_state=RANDOM_SEED,
        n_jobs=1 # CPU constraint
    )

    logger.info("Starting RandomizedSearchCV for hyperparameter tuning...")
    
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_distributions,
        n_iter=20, # k=20 iterations as a reasonable balance
        scoring='r2',
        cv=5,
        verbose=1,
        random_state=RANDOM_SEED,
        n_jobs=1
    )
    
    search.fit(X_train, y_train)
    
    best_model = search.best_estimator_
    logger.info(f"Best parameters found: {search.best_params_}")
    logger.info(f"Best CV score (R2): {search.best_score_:.4f}")
    
    return best_model

def evaluate_model(model: XGBRegressor, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    """
    Evaluate the model on the held-out test set.
    Metrics: R², RMSE, MAPE.
    """
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mape = mean_absolute_percentage_error(y_test, y_pred)
    
    metrics = {
        'r2': float(r2),
        'rmse': float(rmse),
        'mape': float(mape)
    }
    
    logger.info(f"Test Set Metrics: R²={r2:.4f}, RMSE={rmse:.4f}, MAPE={mape:.4f}")
    return metrics

def save_model_and_metrics(model: XGBRegressor, metrics: Dict[str, float]) -> None:
    """
    Save the trained model and metrics to artifacts.
    """
    # Ensure directories exist
    model_dir = Path("models")
    report_dir = Path("artifacts/reports")
    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = model_dir / "best_model.json"
    # XGBoost can save to json
    model.save_model(str(model_path))
    logger.info(f"Model saved to {model_path}")
    
    # Also save as joblib for sklearn compatibility if needed
    joblib.dump(model, model_dir / "best_model.pkl")
    
    # Save metrics
    report_path = report_dir / "training_metrics.json"
    
    # Get threshold justification
    threshold = get_r2_threshold()
    justification = get_threshold_justification()
    
    report_data = {
        'metrics': metrics,
        'threshold_config': {
            'r2_threshold': threshold,
            'justification': justification
        },
        'training_info': {
            'random_seed': RANDOM_SEED,
            'split_ratios': {'train': TRAIN_RATIO, 'val': VAL_RATIO, 'test': TEST_RATIO}
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Metrics report saved to {report_path}")

def main():
    """
    Main execution flow for training.
    """
    set_random_seed(RANDOM_SEED)
    
    try:
        # 1. Load Data
        df = load_and_prepare_data()
        
        # 2. Split Data (70/15/15)
        train_df, val_df, test_df = split_data(df)
        
        target_col = 'diffusivity'
        X_train = train_df.drop(columns=[target_col])
        y_train = train_df[target_col]
        
        X_val = val_df.drop(columns=[target_col])
        y_val = val_df[target_col]
        
        X_test = test_df.drop(columns=[target_col])
        y_test = test_df[target_col]
        
        # 3. Tune Hyperparameters
        best_model = tune_hyperparameters(X_train, y_train, X_val, y_val)
        
        # 4. Evaluate on Test Set
        metrics = evaluate_model(best_model, X_test, y_test)
        
        # 5. Save Artifacts
        save_model_and_metrics(best_model, metrics)
        
        logger.info("Training pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()